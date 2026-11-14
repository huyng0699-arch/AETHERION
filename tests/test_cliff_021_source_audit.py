"""Regression guard for resolved NASA 2023 CliFF Dental Exposed Pulp source (Q-0457).

Verifies that qa/CLIFF-021.json and records/CLIFF-021.json match on SHA-256,
official NASA source provenance, extracted counts, and reject tampered claims.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import unittest
from urllib.parse import urlparse

CLIFF_DIR = Path(__file__).resolve().parents[1] / "knowledge" / "nasa" / "cliff_119_2023"
AUDIT_PATH = CLIFF_DIR / "qa" / "CLIFF-021.json"
RECORD_PATH = CLIFF_DIR / "records" / "CLIFF-021.json"


def validate_resolved_audit(audit: dict, record: dict | None = None) -> None:
    """Reject tampered or unverified source/media/provenance claims."""
    if audit.get("article_id") != "CLIFF-021" or audit.get("slot") != 21:
        raise ValueError("wrong source slot or article identifier")
    if int(audit.get("http_status", 0)) != 200:
        raise ValueError("direct NASA PDF download did not return HTTP 200")
    url = urlparse(str(audit.get("source_direct_url", "")))
    if url.scheme != "https" or url.hostname not in ("nasa.gov", "www.nasa.gov"):
        raise ValueError("source_direct_url must be an official HTTPS nasa.gov document")
    digest = str(audit.get("pdf_sha256", ""))
    if not re.fullmatch(r"[a-f0-9]{64}", digest) or int(audit.get("pdf_bytes", 0)) <= 0:
        raise ValueError("missing verified PDF byte size or SHA-256 digest")
    if audit.get("missing_items") != []:
        raise ValueError("resolved audit must not have unresolved missing_items")
    media_hashes = audit.get("media_sha256s", [])
    if int(audit.get("media_count", -1)) != len(media_hashes) or len(media_hashes) < 1:
        raise ValueError("media_count mismatch with media_sha256s")
    if record is not None:
        if record.get("article_id") != "CLIFF-021" or record.get("completeness_state") != "COMPLETE":
            raise ValueError("record completeness state mismatch")
        src = record.get("source", {})
        if src.get("verification_state") != "VERIFIED" or src.get("content_sha256") != digest:
            raise ValueError("record SHA-256 mismatch with QA audit")


class Cliff021SourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        cls.record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))

    def test_resolved_nasa_2023_slot_and_record_parity(self) -> None:
        validate_resolved_audit(self.audit, self.record)
        self.assertEqual(self.audit["pdf_pages"], 13)
        self.assertEqual(self.audit["sections_count"], 13)
        self.assertEqual(self.audit["tables_count"], 6)
        self.assertIn("PASS", self.audit["license_audit"])
        self.assertIn("PASS", self.audit["content_safety"])

    def test_false_non_nasa_source_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.audit)
        tampered["source_direct_url"] = "https://example.com/fake.pdf"
        with self.assertRaises(ValueError):
            validate_resolved_audit(tampered, self.record)

    def test_false_hash_or_missing_items_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.audit)
        tampered["pdf_sha256"] = "not-a-sha256"
        with self.assertRaises(ValueError):
            validate_resolved_audit(tampered, self.record)
        tampered2 = copy.deepcopy(self.audit)
        tampered2["missing_items"] = ["pdf"]
        with self.assertRaises(ValueError):
            validate_resolved_audit(tampered2, self.record)

    def test_false_media_count_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.audit)
        tampered["media_count"] = 99
        with self.assertRaises(ValueError):
            validate_resolved_audit(tampered, self.record)


if __name__ == "__main__":
    unittest.main()
