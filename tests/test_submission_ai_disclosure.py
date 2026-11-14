from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "submission" / "AI_DISCLOSURE.md"


class TestSubmissionAiDisclosure(unittest.TestCase):
    def test_ai_disclosure_covers_tools_and_safety_limits(self) -> None:
        self.assertTrue(DOC_PATH.is_file(), f"Missing {DOC_PATH}")
        text = DOC_PATH.read_text(encoding="utf-8")

        for required in (
            "Team TRUY TINH",
            "Codex",
            "Antigravity",
            "No Mandatory AI Dependency",
            "Not a Safety-Critical or Clinical Authority",
            "No Fabricated NASA Records",
            "0/119",
        ):
            self.assertIn(required, text)


if __name__ == "__main__":
    unittest.main()
