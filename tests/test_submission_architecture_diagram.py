from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "submission" / "ARCHITECTURE_DIAGRAM.md"


class TestSubmissionArchitectureDiagram(unittest.TestCase):
    def test_architecture_diagram_reflects_actual_repo_state(self) -> None:
        self.assertTrue(DOC_PATH.is_file(), f"Missing {DOC_PATH}")
        text = DOC_PATH.read_text(encoding="utf-8")

        self.assertIn("```mermaid", text)
        self.assertIn("flowchart TB", text)
        for required in (
            "apps/server/",
            "apps/desktop/",
            "packages/contracts/",
            "knowledge/nasa/",
            "apps/mobile/",
            "apps/watch/",
            "PLANNED ONLY",
        ):
            self.assertIn(required, text)

        # Verify mobile and watch genuinely have no source code yet in repo
        mobile_files = [p.name for p in (ROOT / "apps" / "mobile").iterdir()]
        watch_files = [p.name for p in (ROOT / "apps" / "watch").iterdir()]
        self.assertEqual(mobile_files, ["README.md"])
        self.assertEqual(watch_files, ["README.md"])


if __name__ == "__main__":
    unittest.main()
