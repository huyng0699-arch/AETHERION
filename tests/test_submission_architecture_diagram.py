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

        # Source inventory: Expo is in PREPARE, while Wear OS remains planned.
        mobile = ROOT / "apps" / "mobile"
        watch = ROOT / "apps" / "watch"
        self.assertTrue((mobile / "package.json").is_file())
        self.assertTrue(any(mobile.rglob("*.tsx")) or any(mobile.rglob("*.ts")))
        self.assertIn("PREPARE", text)
        self.assertIn("Android unverified", text)
        self.assertIn("118/119", text)
        self.assertNotIn("apps/mobile/ - PLANNED ONLY", text)
        self.assertTrue((watch / "README.md").is_file())
        self.assertFalse(any(watch.rglob("*.kt")))
        self.assertFalse(any(watch.rglob("*.java")))


if __name__ == "__main__":
    unittest.main()
