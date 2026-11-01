[설계 문서로 돌아가기](../design.md#검증-기록)

# 구조 검사 환경과 검증 한계

당시 기본 Python과 bundled Python에 `PyYAML`이 없어 기존 cached `PyYAML`을 사용했습니다. 새 dependency나 test infrastructure는 추가하지 않았습니다. 프로젝트 루트에서 실행한 명령은 다음과 같습니다.

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=<pyyaml_path> \
/usr/bin/python3 \
  <home>/.codex/skills/.system/skill-creator/scripts/quick_validate.py \
  skills/write-me
```

cache 경로는 로컬 검증 환경이며 배포 패키지의 dependency가 아닙니다. 사용할 수 없으면 `PyYAML`이 있는 기존 환경으로 검사하거나 `NOT_RUN`과 이유를 기록합니다. YAML·링크·파일 범위 검사는 프로젝트에 추가하지 않은 임시 command로 수행했습니다.

- `NOT_RUN`: Codex Desktop 화면의 Skill 목록 갱신·호출. 당시 shared app-server proxy가 응답하지 않았고 UI 도구의 앱 접근도 차단됐습니다. CLI 검증을 화면 확인 결과로 확대하지 않습니다.
- `NOT_RUN`: 실제 파일 편집·외부 게시·메시지 전송·배포. 최초 동작 검증은 대화 입력과 읽기 전용 범위에서 수행했습니다.
- `NOT_RUN`: 실행 도구가 없는 환경의 변경량 계산 분기, 장기 사용·시간 절감 benchmark. 원문이 없는 분기는 검증했습니다.
- `Not applicable`: `lint`, `typecheck`, test suite, build, `git diff --check`. package manifest·application code·Git 저장소가 없어 해당 명령을 정의하지 않았습니다.
- 국립국어원 규범 포털 직접 조회는 `403`이어서 관련 공식 상담 답변으로 주요 규칙을 대조했습니다. 외부 링크의 영구 접근 가능성이나 모든 한국어 문맥의 정확성을 보장하지 않습니다.

자동 선택 검증은 당시 명시·암시·대조 입력 각 1건에 한정됩니다. 구조 검사와 대표 입력 결과로 모든 요청·모델·제품 환경의 동일한 동작을 주장하지 않습니다. 검증 방법은 [Codex eval 안내](https://developers.openai.com/blog/eval-skills)를 참고합니다.
