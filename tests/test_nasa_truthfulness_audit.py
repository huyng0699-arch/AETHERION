from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_nasa_truthfulness import audit_truthfulness


class TestNasaTruthfulnessAudit(unittest.TestCase):
    def test_repo_passes_truthfulness_and_branding_audit(self) -> None:
        findings = audit_truthfulness()
        self.assertEqual(findings, [], f"Truthfulness findings: {findings}")

    def test_negative_detects_fabricated_telemetry_and_false_nasa_branding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nasa = root / "knowledge" / "nasa"
            sub = root / "submission"
            nasa.mkdir(parents=True)
            sub.mkdir(parents=True)

            (nasa / "fake_live.json").write_text(
                json.dumps({"is_live_telemetry": True}),
                encoding="utf-8",
            )
            (nasa / "cliff_119_status.json").write_text(
                json.dumps({"is_119_complete": True, "verified_pdf_count": 0}),
                encoding="utf-8",
            )
            (sub / "BAD.md").write_text(
                "This app is endorsed by NASA and flight-certified.",
                encoding="utf-8",
            )

            findings = audit_truthfulness(root)
            self.assertTrue(any("is_live_telemetry" in f for f in findings))
            self.assertTrue(any("fabricated 119 completeness" in f for f in findings))
            self.assertTrue(any("endorsed by nasa" in f.lower() for f in findings))
            self.assertTrue(any("flight" in f.lower() for f in findings))


if __name__ == "__main__":
    unittest.main()
