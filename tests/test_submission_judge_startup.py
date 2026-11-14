import unittest
from pathlib import Path


class JudgeStartupGuideTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.guide = self.root / "submission" / "JUDGE_STARTUP.md"

    def test_judge_startup_guide_exists_and_references_real_scripts(self) -> None:
        self.assertTrue(self.guide.is_file(), "submission/JUDGE_STARTUP.md must exist")
        text = self.guide.read_text(encoding="utf-8")
        normalized = text.replace("\\", "/")

        required_scripts = [
            "scripts/setup_windows.ps1",
            "scripts/start_server.ps1",
            "scripts/start_desktop.ps1",
            "scripts/quest_board.py",
            "scripts/lint_python.py",
        ]
        for rel in required_scripts:
            self.assertIn(rel, normalized)
            self.assertTrue((self.root / rel).is_file(), f"Referenced script missing: {rel}")

        for token in (
            "aetherion_server.main:app",
            "aetherion_desktop",
            "127.0.0.1:8765/health",
            "8765",
            "**not** a NASA product",
        ):
            self.assertIn(token, text)


if __name__ == "__main__":
    unittest.main()
