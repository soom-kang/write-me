"""Claude Code·Codex CLI로 cases.json의 사례를 실행하고 결정적으로 판정합니다.

사용 예:
    python3 evals/run.py --cli claude --runs 3
    python3 evals/run.py --cli claude,codex --case notice-bookclub --case arithmetic

- 각 회차는 빈 임시 디렉터리와 새 세션에서 실행합니다. 입력은 stdin으로만 전달합니다.
- Claude Code는 기본으로 이 저장소의 `skills/write-me`를 임시 프로젝트 Skill로 복사하고
  `--setting-sources project`로 실행합니다. 사용자 설치본을 쓰려면 `--claude-skills installed`.
- Codex도 기본으로 같은 Skill을 임시 git 저장소의 `.agents/skills`에 복사합니다.
  사용자 설치본을 쓰려면 `--codex-skills installed`(저장소와 hash가 다르면 경고).
- 각 결과의 `skill_paths`에 실제로 읽은 SKILL.md 경로를 남깁니다.
- 결과는 `evals/results/<label>/<cli>/<case>-<run>.json`에 저장합니다(gitignore 대상).
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check import check, load_cases, overall, print_summary, rescore  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = ROOT / "skills" / "write-me"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
CODEX_SKILL_DIRS = [Path.home() / ".agents/skills/write-me", Path.home() / ".codex/skills/write-me"]
TIMEOUT_SECONDS = 600


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def skill_version():
    for line in (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version:"):
            return line.split(":", 1)[1].strip().strip('"')
    return "unknown"


def claude_command(skill_source):
    command = [
        "claude", "-p", "--tools", "Skill,Read", "--allowedTools", "Skill,Read",
        "--permission-prompts", "none", "--no-session-persistence",
        "--output-format", "stream-json", "--verbose",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--settings", '{"disableAllHooks":true}', "--no-chrome",
    ]
    if skill_source == "project":
        command += ["--setting-sources", "project"]
    else:
        command += ["--add-dir", str(Path.home() / ".claude/skills")]
    return command


def codex_command(cwd):
    return [
        "codex", "--no-daemon", "exec", "--ephemeral", "--sandbox", "read-only",
        "--skip-git-repo-check", "--json", "--color", "never", "-C", str(cwd), "-",
    ]


def skill_paths_in(text):
    return sorted(set(re.findall(r"[^\s'\"]*write-me/SKILL\.md", text)))


def parse_claude(stdout):
    invoked, output, session_id = False, "", None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        session_id = session_id or event.get("session_id")
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") != "tool_use":
                    continue
                payload = json.dumps(block.get("input", {}), ensure_ascii=False)
                if block.get("name") == "Skill" and "write-me" in payload:
                    invoked = True
                if block.get("name") == "Read" and "write-me/SKILL.md" in payload:
                    invoked = True
        if event.get("type") == "result":
            output = event.get("result", "")
    return invoked, output, session_id


def parse_codex(stdout):
    invoked, output, session_id = False, "", None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            session_id = event.get("thread_id")
        item = event.get("item") or {}
        if item.get("type") == "command_execution" and "write-me/SKILL.md" in item.get("command", ""):
            invoked = True
        if event.get("type") == "item.completed" and item.get("type") == "agent_message":
            output = item.get("text", "")
    return invoked, output, session_id


def run_once(cli, case, run, out_dir, skill_source):
    with tempfile.TemporaryDirectory(prefix="write-me-eval-") as cwd:
        if cli == "claude":
            if skill_source["claude"] == "project":
                shutil.copytree(SKILL_DIR, Path(cwd) / ".claude/skills/write-me")
            command, parse = claude_command(skill_source["claude"]), parse_claude
        else:
            if skill_source["codex"] == "project":
                shutil.copytree(SKILL_DIR, Path(cwd) / ".agents/skills/write-me")
                subprocess.run(["git", "init", "-q", cwd], check=True)
            command, parse = codex_command(cwd), parse_codex
        started = time.monotonic()
        try:
            proc = subprocess.run(
                command, input=case["prompt"], capture_output=True, text=True,
                cwd=cwd, timeout=TIMEOUT_SECONDS,
            )
            returncode, stdout, stderr = proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired:
            returncode, stdout, stderr = None, "", "timeout"
    invoked, output, session_id = parse(stdout)
    if returncode != 0:
        invoked = None
    record = {
        "case_id": case["id"], "cli": cli, "run": run, "invoked": invoked, "output": output,
        "skill_paths": skill_paths_in(stdout),
        "session_id": session_id, "returncode": returncode,
        "stderr_tail": stderr[-500:] if returncode != 0 else "",
        "elapsed_seconds": round(time.monotonic() - started, 1),
    }
    path = out_dir / cli / f"{case['id']}-{run}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status = overall(check(case, invoked, output))
    stray = [p for p in record["skill_paths"] if skill_source[cli] == "project" and p.startswith(("/", "~")) and "write-me-eval-" not in p]
    note = f"  경고: 프로젝트 밖 Skill 읽음 {stray}" if stray else ""
    print(f"{status:7} {cli:6} {case['id']:28} #{run}{note}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--cli", default="claude", help="claude, codex 또는 claude,codex")
    parser.add_argument("--case", action="append", help="실행할 사례 id(반복 가능). 생략하면 전체")
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--jobs", type=int, default=2, help="동시에 실행할 회차 수")
    parser.add_argument("--label", help="결과 디렉터리 이름. 기본값은 <version>-<시각>")
    parser.add_argument("--claude-skills", choices=["project", "installed"], default="project")
    parser.add_argument("--codex-skills", choices=["project", "installed"], default="project")
    args = parser.parse_args()

    cases = load_cases()
    selected = [cases[c] for c in args.case] if args.case else list(cases.values())
    clis = [c.strip() for c in args.cli.split(",") if c.strip()]
    label = args.label or f"{skill_version()}-{datetime.now():%Y%m%d-%H%M%S}"
    out_dir = RESULTS_DIR / label

    skill_source = {"claude": args.claude_skills, "codex": args.codex_skills}
    if "codex" in clis and args.codex_skills == "installed":
        installed = next((d for d in CODEX_SKILL_DIRS if (d / "SKILL.md").exists()), None)
        if installed is None:
            sys.exit("Codex 설치본 write-me를 찾지 못했습니다.")
        if sha256(installed / "SKILL.md") != sha256(SKILL_DIR / "SKILL.md"):
            print(f"경고: Codex 설치본 {installed}의 SKILL.md가 저장소와 다릅니다.", file=sys.stderr)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "meta.json").write_text(json.dumps({
        "label": label, "skill_version": skill_version(),
        "skill_sha256": sha256(SKILL_DIR / "SKILL.md"),
        "clis": clis, "skill_source": skill_source, "runs": args.runs,
        "cases": [c["id"] for c in selected], "started_at": datetime.now().isoformat(timespec="seconds"),
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    jobs = [(cli, case, run) for cli in clis for case in selected for run in range(1, args.runs + 1)]
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for future in [pool.submit(run_once, cli, case, run, out_dir, skill_source) for cli, case, run in jobs]:
            future.result()

    print(f"\n# {out_dir.relative_to(ROOT)}")
    print_summary(rescore(out_dir))


if __name__ == "__main__":
    main()
