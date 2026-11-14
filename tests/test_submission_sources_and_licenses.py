from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "submission" / "SOURCES_AND_LICENSES.md"


class TestSubmissionSourcesAndLicenses(unittest.TestCase):
    def test_license_notice_and_registry_hashes_match_submission_doc(self) -> None:
        self.assertTrue(DOC_PATH.is_file(), f"Missing {DOC_PATH}")
        doc = DOC_PATH.read_text(encoding="utf-8")

        for rel in ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md", "knowledge/nasa/source_registry.json"):
            target = ROOT / rel
            self.assertTrue(target.is_file(), f"Missing {target}")
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            self.assertIn(digest, doc, f"SHA-256 for {rel} missing or stale in {DOC_PATH}")

        notice_text = (ROOT / "NOTICE").read_text(encoding="utf-8")
        self.assertIn("Team TRUY TINH", notice_text)
        self.assertIn("NASA is not a sponsor, partner, certifier or endorser", notice_text)
        self.assertIn("Apache-2.0", doc)
        self.assertIn("OSD-575", doc)
        self.assertIn("NOT_IMPORTED", doc)


if __name__ == "__main__":
    unittest.main()
