"""check.py가 docs/design.md에 기록된 과거 판정을 재현하는지 확인합니다.

사용: python3 -m unittest evals/test_check.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from check import check, load_cases, overall  # noqa: E402

CASES = load_cases()

# 0.3.3 후속 검증의 Codex 1 출력 — 범주 불릿 하나에 세 항목을 열거해 FAIL로 기록됨
BOOKCLUB_CATEGORY_BULLET = """동네 도서관 독서모임 신청 페이지에서 자신에게 맞는 모임을 미리 찾아볼 수 있습니다.

- 확인할 수 있는 정보: 모임 주제, 운영 요일, 참가 대상
- 신청 접수: 2026-11-09부터 시작

확정 안내 이메일을 받은 경우에만 참여가 확정됩니다.

페이지는 현재 시범 운영 중이며, 화면에 표시된 남은 정원은 실제 신청 현황과 다를 수 있습니다.
"""

# 같은 검증의 Claude Code 3 출력 — PASS로 기록됨
BOOKCLUB_ITEM_BULLETS = """동네 도서관 독서모임 신청 페이지에서는 참여하려는 이용자가 자신에게 맞는 모임을 미리 찾아볼 수 있습니다. 확인할 수 있는 정보는 다음과 같습니다.

- 모임 주제
- 운영 요일
- 참가 대상

신청은 2026-11-09부터 받으며, 확정 안내 이메일을 받아야 참여가 확정됩니다.

현재 이 페이지는 시범 운영 중입니다. 화면에 표시된 남은 정원은 실제 신청 현황과 다를 수 있습니다.
"""


def status(case_id, invoked, output):
    return overall(check(CASES[case_id], invoked, output))


class CheckTest(unittest.TestCase):
    def test_category_bullet_fails(self):
        self.assertEqual(status("notice-bookclub", True, BOOKCLUB_CATEGORY_BULLET), "FAIL")

    def test_item_bullets_pass(self):
        self.assertEqual(status("notice-bookclub", True, BOOKCLUB_ITEM_BULLETS), "PASS")

    def test_new_causal_link_fails(self):
        output = BOOKCLUB_ITEM_BULLETS.replace("시범 운영 중입니다. 화면에", "시범 운영 중이라 화면에")
        self.assertEqual(status("notice-bookclub", True, output), "FAIL")

    def test_prose_rejects_bullets(self):
        self.assertEqual(status("notice-bookclub-prose", True, BOOKCLUB_ITEM_BULLETS), "FAIL")

    def test_missed_invocation_fails(self):
        self.assertEqual(status("notice-bookclub", False, BOOKCLUB_ITEM_BULLETS), "FAIL")

    def test_unknown_invocation_is_not_run(self):
        self.assertEqual(status("notice-bookclub", None, BOOKCLUB_ITEM_BULLETS), "NOT_RUN")

    def test_negative_case(self):
        self.assertEqual(status("arithmetic", False, "4"), "PASS")
        self.assertEqual(status("arithmetic", True, "4"), "FAIL")

    def test_unchanged(self):
        original = CASES["already-natural"]["expect"]["original"]
        self.assertEqual(status("already-natural", True, original + "\n"), "PASS")
        self.assertEqual(status("already-natural", True, "회의는 오후 3시에 시작합니다."), "FAIL")


if __name__ == "__main__":
    unittest.main()
