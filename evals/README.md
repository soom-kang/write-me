# 회귀 평가

`docs/design.md`의 버전별 검증 입력을 저장소에 고정해, 지침을 바꾼 뒤 같은 입력으로 다시 확인합니다.

| 파일 | 역할 |
|---|---|
| `cases.json` | 사례별 입력, 호출 기대값, 형식(`bullets`·`prose`·`unchanged`·`any`), 필수·금지 정규식, 사람이 판단할 rubric |
| `check.py` | 저장된 결과를 결정적으로 다시 판정 |
| `run.py` | Claude Code·Codex CLI로 사례를 실행하고 결과를 `results/<label>/`에 저장 |
| `test_check.py` | 과거 기록의 실패·통과 출력을 `check.py`가 같게 판정하는지 확인 |

## 실행

Python 3.10 이상의 표준 라이브러리만 사용합니다. 각 회차는 빈 임시 디렉터리와 새 세션에서 실행합니다.

```bash
python3 -m unittest evals/test_check.py
```

```bash
python3 evals/run.py --cli claude,codex --runs 3
```

```bash
python3 evals/check.py evals/results/<label>
```

- `--case <id>`를 반복해 일부 사례만 실행합니다.
- Claude Code는 기본으로 저장소의 `skills/write-me`를 임시 프로젝트 Skill로 복사하고 `--setting-sources project`로 실행합니다. 따라서 사용자 Skill과의 선택 경쟁은 빠집니다. 과거 검증과 같은 조건이 필요하면 `--claude-skills installed`를 씁니다.
- Codex도 기본으로 저장소 Skill을 임시 git 저장소의 `.agents/skills`에 복사해 실행합니다. 사용자 설치본을 쓰려면 `--codex-skills installed`를 씁니다(저장소와 다르면 경고).
- 결과의 `skill_paths`에 실제로 읽은 `SKILL.md` 경로가 남습니다. 프로젝트 모드에서 사용자 설치본을 읽으면 실행 중 경고합니다.
- `evals/baselines/`에는 버전별 실행 요약을 commit합니다.
- 실행에는 모델 사용량이 듭니다. 전체 15개 사례를 두 CLI에서 3회씩 돌리면 90회 요청입니다.

## 판정 범위

`check.py`는 호출 여부, 불릿 분리, 산문 유지, 보호 정보, 금지 표현만 판정합니다. 의미 보존과 새 인과관계 같은 판단은 `rubric`을 보고 사람이 확인하거나 별도 문맥의 모델 검토로 확인합니다. 결정적 판정의 `PASS`를 rubric 통과로 해석하지 않습니다.

사례를 추가할 때는 실패를 재현하는 입력을 먼저 넣고, 지침을 고친 뒤 같은 사례로 확인합니다. 실패한 출력은 `test_check.py`에 넣어 판정 기준이 그 실패를 잡는지 고정합니다.
