from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_cliff_119 import EXPECTED_COUNT, audit_cliff_directory

ROOT = Path(__file__).resolve().parents[1]
STATUS_JSON = ROOT / "knowledge" / "nasa" / "cliff_119_status.json"


class TestCliff119Status(unittest.TestCase):
    def test_repo_status_is_honestly_not_imported(self) -> None:
        self.assertTrue(STATUS_JSON.is_file(), f"Missing {STATUS_JSON}")
        report = json.loads(STATUS_JSON.read_text(encoding="utf-8"))
        self.assertEqual(report["expected_count"], EXPECTED_COUNT)
        self.assertEqual(report["verified_pdf_count"], 0)
        self.assertFalse(report["is_119_complete"])
        self.assertEqual(report["verification_status"], "NOT_IMPORTED")
        self.assertTrue(report["not_live_crew_telemetry"])

    def test_negative_fake_pdf_and_hash_mismatch_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            orig = base / "original"
            orig.mkdir()
            # Write a fake non-PDF file with .pdf extension
            fake = orig / "fake.pdf"
            fake.write_bytes(b"NOT A REAL PDF")
            # Write a real PDF header file with wrong manifest hash
            real = orig / "real.pdf"
            real.write_bytes(b"%PDF-1.4\n%fake-body\n")
            (base / "manifest.json").write_text(
                json.dumps(
                    {
                        "documents": [
                            {"filename": "real.pdf", "sha256": "0" * 64},
                            {"filename": "missing.pdf", "sha256": hashlib.sha256(b"x").hexdigest()},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            report = audit_cliff_directory(base, checked_at_utc="2026-11-14T03:50:00Z")
            self.assertEqual(report["verified_pdf_count"], 1)
            self.assertEqual(report["invalid_pdf_files"], ["fake.pdf"])
            self.assertIn("sha256_mismatch:real.pdf", report["manifest_mismatches"])
            self.assertIn("missing:missing.pdf", report["manifest_mismatches"])
            self.assertFalse(report["is_119_complete"])
            self.assertEqual(report["verification_status"], "PARTIAL_OR_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
