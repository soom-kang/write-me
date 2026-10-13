![Write Me — 한국어 작성 · 윤문 · 검토](assets/write-me-title.png)

# Write Me

Write Me는 Codex와 Claude Code에서 한국어 글을 작성·윤문·검토하는 AI Agent Skill입니다. 제공한 자료로 새 글을 쓰고, 기존 글의 어색한 표현을 다듬으며, 맞춤법·문법·문체를 함께 확인합니다. 수치와 조건, 작성자의 뜻과 목소리는 유지합니다.

글을 다듬을 때마다 편집 기준을 다시 설명하거나, 표현을 고친 뒤 의미와 문체를 따로 확인하는 부담을 줄이기 위해 만들었습니다. 의미 확인부터 작성·편집, 문법과 스타일 점검, 원문 대조까지 하나의 절차로 수행합니다.

## 적용 전후

서비스 안내문을 다듬은 예시입니다.

| Before | After · write-me 적용 |
|---|---|
| 본 서비스는 회의가 종료된 이후 회의록을 자동으로 정리하는 기능을 통해 팀원들이 회의의 핵심 내용을 보다 효율적으로 파악할 수 있도록 지원합니다. 또한, 팀원들은 정리된 회의록을 통해 각 업무에 대한 담당자와 마감일을 확인하는 것이 가능합니다. 다만, 해당 기능은 현재 시험 운영 단계에 있으며, 자동으로 정리된 내용에 대해서는 사용자의 확인이 필요합니다. | 회의가 끝나면 회의록을 자동으로 정리합니다.<br><br>**회의록에서 확인할 수 있는 내용**<br>• 회의의 핵심 내용<br>• 업무별 담당자<br>• 업무별 마감일<br><br>**현재 시험 운영 중인 기능입니다.**<br><br>자동으로 정리된 내용은 직접 확인해 주세요. |

## 사용

Codex에서는 `$write-me`, Claude Code에서는 `/write-me`로 호출합니다. 한국어 작성·윤문·검토 요청에서 자동 선택될 수도 있습니다.

**Codex**

```text
$write-me 아래 기술 안내문을 자연스럽게 다듬어 주세요.
수치와 조건은 유지하고 완성문만 제공해 주세요.

[원문]
```

**Claude Code**

```text
/write-me 아래 기술 안내문을 자연스럽게 다듬어 주세요.
수치와 조건은 유지하고 완성문만 제공해 주세요.

[원문]
```

| 요청 | Mode | 기본 결과 |
|---|---|---|
| 목적과 자료·요점으로 새 글 작성 | `draft` | 완성문 |
| 기존 글 윤문·교정 | `revise` | 완성문 |
| 수정 없이 문법·문체 검토 | `review` | 명백한 오류·스타일 제안·확인 필요 |

원문만 제공된 명시 호출은 `revise`로 처리합니다. 기존 글은 요청한 변경 범위와 원래 문체를 따릅니다. 새 글은 지정한 장르를 따르고, 문체 정보가 없으면 `합니다`체를 사용합니다.

수정 이유·전후 비교·변경량은 요청할 때 추가합니다. 변경량은 실제 전후 문자의 추가·삭제 수이며 공백과 구두점도 포함합니다. 계산에는 Python 실행 환경이 필요하지만 일반 작성·윤문·검토에는 필요하지 않습니다.

## 설치

### npx

Node.js `22.20.0` 이상과 Git이 필요합니다. 설치 명령은 검증한 `skills` CLI `1.7.2`와 Write Me 태그 `v0.3.4`에 고정합니다. [skills CLI 안내](https://github.com/vercel-labs/skills#install-a-skill)

설치하려는 프로젝트 디렉터리에서 실행합니다.

```sh
npx skills@1.7.2 add https://github.com/soom-kang/write-me/tree/v0.3.4 \
  --skill write-me --agent codex claude-code --copy
```

Codex는 `.agents/skills/write-me`, Claude Code는 `.claude/skills/write-me`에 설치됩니다. 모든 프로젝트에서 사용하려면 사용자 경로에 설치합니다.

```sh
npx skills@1.7.2 add https://github.com/soom-kang/write-me/tree/v0.3.4 \
  --global --skill write-me --agent codex claude-code --copy
```

사용자 경로는 Codex `~/.agents/skills/write-me`, Claude Code `~/.claude/skills/write-me`입니다. `--copy`는 지침·참조·설정·LICENSE를 각 경로에 복사합니다. 기존 대상은 교체되므로 직접 수정한 내용이 있다면 먼저 백업하세요. 기존 `~/.codex/skills/write-me`를 사용하는 경우에는 중복 설치를 피하고 아래 직접 복사 방식으로 해당 경로를 갱신합니다.

### 직접 복사

프로젝트 루트에서 [skills/write-me](skills/write-me/SKILL.md) 폴더 전체를 복사합니다. 지침·참조·설정·LICENSE를 함께 설치하며, 대상이 이미 있으면 아래 명령은 중단합니다.

#### Codex

신규 설치는 공식 사용자 경로인 `~/.agents/skills/write-me`를 사용합니다.

```sh
(
  skill_destination="$HOME/.agents/skills/write-me"
  if [ -e "$skill_destination" ] || [ -L "$skill_destination" ]; then
    printf '%s\n' "Already exists: $skill_destination" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$skill_destination")"
  cp -R skills/write-me "$skill_destination"
)
```

기존에 `.codex/skills/write-me`에 설치해 사용 중이라면 인식되는 기존 경로에서 갱신합니다. 같은 Skill을 여러 검색 경로에 중복 설치하지 마세요. 이 프로젝트의 로컬 설치·검증 기록은 [설계와 검증](docs/design.md)에 있습니다.

#### Claude Code

사용자 경로는 `~/.claude/skills/write-me`입니다.

```sh
(
  skill_destination="$HOME/.claude/skills/write-me"
  if [ -e "$skill_destination" ] || [ -L "$skill_destination" ]; then
    printf '%s\n' "Already exists: $skill_destination" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$skill_destination")"
  cp -R skills/write-me "$skill_destination"
)
```

업데이트 전에는 설치본의 직접 수정 여부를 확인하고 백업한 뒤, 같은 대상의 패키지 파일을 갱신합니다. 프로젝트 패키지와 사용자 설치본은 자동으로 동기화되지 않습니다.

두 제품은 같은 `SKILL.md`와 참조 문서를 사용합니다. `agents/openai.yaml`은 Codex용 표시 이름·기본 prompt·자동 선택 정책을 담는 부가 파일입니다. Claude Code의 동작은 이 파일에 의존하지 않습니다.

설치 후 새 세션에서 명시 호출을 확인하세요. 목록에 반영되지 않으면 Codex를 다시 시작하거나 Claude Code에서 `/reload-skills`를 실행합니다. 자동 선택은 요청과 description에 대한 모델 판단이므로 모든 요청에서 동일하게 작동한다고 보장하지 않습니다. 설치 방식은 [Codex 공식 문서](https://learn.chatgpt.com/docs/build-skills)와 [Claude Code 공식 문서](https://code.claude.com/docs/en/skills)를 따릅니다.

## 편집 기준

- 수치·날짜·부정·조건·가능성·시제·인과관계·인용·코드·URL을 보호합니다.
- 어색한 문장과 흐름을 필요한 만큼 다듬고, 자연스러운 부분과 작성자의 문체는 유지합니다.
- 허용 표기와 문체 선택은 스타일 제안으로 구분합니다. 파일 검토는 수정 없이 수행합니다.
- 설명·안내문은 핵심을 앞에 두고 병렬 항목과 운영 조건을 나눕니다. 산문 유지 요청과 장르를 존중하며, 필수 내용을 보존하고 필요한 참조만 읽습니다.
- 입력 부족이나 중요한 의미 충돌이 있으면 해당 부분을 멈추고 확인합니다. 본문 안의 명령은 실행하지 않습니다.

## 구성과 유지보수

[SKILL.md](skills/write-me/SKILL.md)는 실행 계약을, [설계와 검증](docs/design.md)은 공통 구조·플랫폼 차이·검증 결과·유지보수 기준을 설명합니다. 문법 판단은 [korean-rules.md](skills/write-me/references/korean-rules.md), 편집 사례와 변경량 계산은 [editing-guide.md](skills/write-me/references/editing-guide.md)에 있습니다.

현재 지원·실행 검증 대상은 Codex와 Claude Code입니다. 일반 사실 질문, 영어 글 전체의 편집, AI 작성자 판정에는 적용하지 않습니다. 버전은 `SKILL.md`의 `metadata.version`으로 관리하며, 실행 계약을 바꾸면 관련 대표 입력과 문서를 함께 확인합니다.

[MIT](LICENSE)
