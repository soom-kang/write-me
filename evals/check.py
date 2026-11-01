"""cases.json의 기대 조건으로 실행 결과를 결정적으로 판정합니다.

사용:
    python3 evals/check.py evals/results/<label>
결과 디렉터리의 */*.json을 다시 판정해 요약을 출력합니다. 표준 라이브러리만 사용합니다.
"""

import json
import re
import sys
from pathlib import Path

CASES_PATH = Path(__file__).with_name("cases.json")
BULLET_RE = re.compile(r"^\s*(?:[-*•·]|\d+[.)])\s+")
HEADING_RE = re.compile(r"^\s*(?:#{1,6}\s|\*\*[^*]+\*\*\s*$)")
FENCE_RE = re.compile(r"^\s*```")


def load_cases(path=CASES_PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {case["id"]: case for case in data["cases"]}


def normalize(text):
    return re.sub(r"\s+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def strip_fences(text):
    return "\n".join(line for line in text.splitlines() if not FENCE_RE.match(line))


def bullet_lines(text):
    return [line for line in text.splitlines() if BULLET_RE.match(line)]


def assign_groups(groups, lines):
    """각 그룹을 서로 다른 불릿 줄에 배정할 수 있는지 확인합니다. 실패한 그룹을 돌려줍니다."""
    candidates = [
        [i for i, line in enumerate(lines) if any(alt in line for alt in group)]
        for group in groups
    ]
    order = sorted(range(len(groups)), key=lambda g: len(candidates[g]))
    used = {}

    def place(k):
        if k == len(order):
            return True
        g = order[k]
        for i in candidates[g]:
            if i not in used:
                used[i] = g
                if place(k + 1):
                    return True
                del used[i]
        return False

    if place(0):
        return []
    return [groups[g][0] for g in range(len(groups)) if not candidates[g]] or ["(서로 다른 불릿에 배정 불가)"]


def check(case, invoked, output):
    """판정 목록을 돌려줍니다. 각 항목은 (이름, PASS|FAIL|NOT_RUN, 설명)입니다."""
    expect = case["expect"]
    body = strip_fences(output or "")
    results = []

    if invoked is None:
        results.append(("invoke", "NOT_RUN", "호출 여부를 판별하지 못함"))
    else:
        ok = invoked == expect["invoke"]
        results.append(("invoke", "PASS" if ok else "FAIL", f"expected={expect['invoke']} actual={invoked}"))

    fmt = expect.get("format", "any")
    bullets = bullet_lines(body)
    if fmt == "bullets":
        missing = assign_groups(expect.get("bullets", []), bullets) if bullets else ["(불릿 없음)"]
        results.append(("format:bullets", "FAIL" if missing else "PASS", ", ".join(missing)))
    elif fmt == "prose":
        structured = [line for line in body.splitlines() if BULLET_RE.match(line) or HEADING_RE.match(line)]
        results.append(("format:prose", "FAIL" if structured else "PASS", structured[0].strip() if structured else ""))
    elif fmt == "unchanged":
        ok = normalize(body) == normalize(expect["original"])
        results.append(("format:unchanged", "PASS" if ok else "FAIL", "" if ok else normalize(body)[:80]))

    for pattern in expect.get("require", []):
        ok = re.search(pattern, body) is not None
        results.append((f"require:{pattern}", "PASS" if ok else "FAIL", ""))
    for pattern in expect.get("forbid", []):
        match = re.search(pattern, body)
        results.append((f"forbid:{pattern}", "FAIL" if match else "PASS", match.group(0) if match else ""))
    return results


def overall(results):
    statuses = {status for _, status, _ in results}
    if "FAIL" in statuses:
        return "FAIL"
    if "NOT_RUN" in statuses:
        return "NOT_RUN"
    return "PASS"


def rescore(results_dir):
    cases = load_cases()
    rows = []
    for path in sorted(Path(results_dir).glob("*/*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        case = cases.get(record["case_id"])
        if case is None:
            continue
        results = check(case, record.get("invoked"), record.get("output", ""))
        rows.append((record["cli"], record["case_id"], record["run"], overall(results), results))
    return rows


def print_summary(rows):
    for cli, case_id, run, status, results in rows:
        failed = [f"{name}{f' ({detail})' if detail else ''}" for name, s, detail in results if s != "PASS"]
        print(f"{status:7} {cli:6} {case_id:28} #{run}  {'; '.join(failed)}")
    counts = {}
    for _, _, _, status, _ in rows:
        counts[status] = counts.get(status, 0) + 1
    print(" · ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "결과 없음")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python3 evals/check.py <results_dir>")
    print_summary(rescore(sys.argv[1]))
