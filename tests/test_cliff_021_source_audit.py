"""Regression guard for the unverified NASA 2023 CliFF Dental Exposed Pulp source.

This intentionally does NOT pretend the missing 2023 PDF or a native Windows
reader was tested. It verifies that the committed source audit stays honest.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest
from urllib.parse import urlparse

AUDIT_PATH = (
    Path(__file__).resolve().parents[1]
    / "knowledge/nasa/cliff_119_2023/qa/CLIFF-021.json"
)


def validate_blocked_audit(audit: dict) -> None:
    """Reject a false-positive source/clinical/media success claim."""
    if audit["quest_id"] != "Q-0321" or audit["source_slot"] != 21:
        raise ValueError("wrong source slot")
    if audit["article_id"] != "CLIFF-021":
        raise ValueError("wrong article identifier")
    if audit["status"] != "BLOCKED_ORIGINAL_DOCUMENT_LINK_UNVERIFIED":
        raise ValueError("the audit describes an unverified, blocked source")
    index = audit["index"]
    if index["source_pdf_link_verified"] or index["original_document_url"]:
        raise ValueError("an unverified PDF cannot have an approved source link")
    if index["dental_2023_item_is_clickable_in_rendered_page"]:
        raise ValueError("the rendered 2023 index item has not been linked")
    extraction = audit["extraction"]
    if extraction["original_bytes_downloaded"] or extraction["original_pdf_sha256"]:
        raise ValueError("the original 2023 PDF was not downloaded or hashed")
    for key in (
        "source_pages_verified", "sections_imported", "tables_imported",
        "figures_imported", "licensed_medical_image_blobs"
    ):
        if extraction[key] != 0:
            raise ValueError(f"false completed extraction claim: {key}")
    for key in (
        "full_source_text_provided", "imported_to_library_sqlite",
        "native_windows_reader_proven", "clinical_content_accepted"
    ):
        if extraction[key]:
            raise ValueError(f"false completed acceptance claim: {key}")
    if extraction["independent_review"] != "PENDING":
        raise ValueError("independent review is not complete")


class Cliff021SourceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

    def test_exact_nasa_2023_slot_and_source_family(self) -> None:
        audit = self.audit
        self.assertEqual(audit["display_title"], "Dental Exposed Pulp")
        self.assertEqual(audit["source_category"], "Dental Injury")
        self.assertEqual(audit["source_family"], "CliFF 119 (2023)")
        self.assertEqual(audit["index"]["evidence_text"], "Dental Exposed Pulp CliFF (2023)")
        self.assertEqual(audit["index"]["indicated_source_family"], "CliFF 119")
        self.assertEqual(urlparse(audit["index"]["url"]).hostname, "www.nasa.gov")

    def test_missing_original_is_not_claimed_healthy_or_downloaded(self) -> None:
        validate_blocked_audit(self.audit)
        self.assertEqual(
            self.audit["index"]["pdf_http_status"],
            "NOT_ATTEMPTED_NO_VERIFIED_DIRECT_URL"
        )
        self.assertIsNone(self.audit["extraction"]["original_pdf_bytes"])

    def test_2016_alternative_is_explicitly_excluded(self) -> None:
        context = self.audit["independent_context"]
        self.assertTrue(context)
        for item in context:
            self.assertFalse(item["considered_for_ingestion"])
            self.assertNotEqual(item["url"], self.audit["index"]["original_document_url"])
        self.assertTrue(any("2016" in item["relation"] for item in context))

    def test_blocker_and_next_action_are_specific(self) -> None:
        self.assertGreaterEqual(len(self.audit["blocking_requirements"]), 4)
        self.assertIn("2023", self.audit["next_action"])
        self.assertIn("not nonexistence", self.audit["evidence_qualification"])

    def test_false_verified_document_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.audit)
        tampered["index"]["source_pdf_link_verified"] = True
        tampered["index"]["original_document_url"] = "https://example.com/fake.pdf"
        with self.assertRaises(ValueError):
            validate_blocked_audit(tampered)

    def test_false_offline_acceptance_is_rejected(self) -> None:
        tampered = copy.deepcopy(self.audit)
        tampered["extraction"]["native_windows_reader_proven"] = True
        with self.assertRaises(ValueError):
            validate_blocked_audit(tampered)

    def test_false_medical_images_are_rejected(self) -> None:
        tampered = copy.deepcopy(self.audit)
        tampered["extraction"]["licensed_medical_image_blobs"] = 3
        with self.assertRaises(ValueError):
            validate_blocked_audit(tampered)


if __name__ == "__main__":
    unittest.main()
