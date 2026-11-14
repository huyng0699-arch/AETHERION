"""Tests for Q-0421 verified NASA CliFF import pipeline and idempotent transactions."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from knowledge.nasa.cliff_119_2023 import library_schema
from knowledge.nasa.cliff_119_2023.importer import (
    ImportValidationError,
    ingest_article_record,
    ingest_directory,
)

# Minimal 1x1 PNG bytes for synthetic ingestion test only
SYNTHETIC_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0"
    b"\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _make_sample_record(png_sha: str) -> dict:
    return {
        "article_id": "CLIFF-001",
        "slot": 1,
        "display_title": "Synthetic Test Fixture — Abdominal Injury",
        "category": "Abdominal Injury",
        "article_version": "2023.1",
        "completeness_state": "COMPLETE",
        "source_notes": "Synthetic engineering test fixture only; not NASA medical content.",
        "source": {
            "source_id": "SRC-CLIFF-001",
            "publisher": "NASA",
            "title": "Synthetic CliFF Test Source",
            "source_url": "https://www.nasa.gov/integrated-medical-model-documentation/",
            "content_sha256": "a" * 64,
            "license_identifier": "US_GOV_PUBLIC_DOMAIN",
            "attribution": "NASA Synthetic Test Fixture",
            "verification_state": "VERIFIED",
        },
        "sections": [
            {
                "heading": "1. Scope",
                "text_content": "Synthetic test paragraph.",
                "page_start": 1,
                "page_end": 1,
                "source_anchor": "p.1",
            }
        ],
        "tables": [
            {
                "title": "Table 1",
                "rows": [["Metric", "Value"], ["Sample", "1.0"]],
                "page_number": 1,
                "source_anchor": "p.1",
            }
        ],
        "media": [
            {
                "media_id": "MED-001",
                "media_kind": "DIAGRAM",
                "data_bytes": SYNTHETIC_PNG,
                "mime_type": "image/png",
                "width": 1,
                "height": 1,
                "sha256": png_sha,
                "creator": "Synthetic Test",
                "license_identifier": "CC0-1.0",
                "source_url": "https://example.invalid/sample.png",
                "attribution": "Synthetic Test",
                "caption": "Synthetic 1x1 test image",
                "alt_text": "1x1 pixel",
                "page_number": 1,
                "usage_review": "APPROVED",
            }
        ],
        "references": [
            {
                "label": "NASA IMM Docs",
                "citation_url": "https://www.nasa.gov/integrated-medical-model-documentation/",
                "page_number": 1,
            }
        ],
    }


class CliffImporterTests(unittest.TestCase):
    def test_idempotent_ingest_and_directory_import(self) -> None:
        png_sha = hashlib.sha256(SYNTHETIC_PNG).hexdigest()
        record = _make_sample_record(png_sha)

        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "AETHERION_NASA_CLIFF_119.sqlite"
            first = ingest_article_record(db, record)
            second = ingest_article_record(db, record)
            self.assertEqual(first["audit"]["articles"], 1)
            self.assertEqual(second["audit"]["articles"], 1)
            self.assertEqual(second["audit"]["media_assets"], 1)
            self.assertEqual(second["audit"]["media_hash_mismatches"], [])

            # Test incremental directory ingestion with external asset file
            rec_dir = Path(directory) / "records"
            rec_dir.mkdir()
            img_path = Path(directory) / "sample.png"
            img_path.write_bytes(SYNTHETIC_PNG)

            file_rec = _make_sample_record(png_sha)
            file_rec["article_id"] = "CLIFF-002"
            file_rec["slot"] = 2
            file_rec["source"]["source_id"] = "SRC-CLIFF-002"
            file_rec["media"][0].pop("data_bytes")
            file_rec["media"][0]["media_id"] = "MED-002"
            file_rec["media"][0]["file_path"] = "sample.png"
            (rec_dir / "CLIFF-002.json").write_text(json.dumps(file_rec), encoding="utf-8")

            dir_res = ingest_directory(db, rec_dir, assets_root=directory)
            self.assertEqual(dir_res["ingested_articles"], ["CLIFF-002"])
            self.assertEqual(dir_res["audit"]["articles"], 2)
            self.assertEqual(dir_res["audit"]["media_assets"], 2)

    def test_rejects_missing_provenance_bad_mime_and_hash_mismatch(self) -> None:
        png_sha = hashlib.sha256(SYNTHETIC_PNG).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "reject.sqlite"

            bad_prov = _make_sample_record(png_sha)
            bad_prov["source"]["license_identifier"] = ""
            with self.assertRaises(ImportValidationError):
                ingest_article_record(db, bad_prov)

            bad_mime = _make_sample_record(png_sha)
            bad_mime["media"][0]["mime_type"] = "application/pdf"
            with self.assertRaises(ImportValidationError):
                ingest_article_record(db, bad_mime)

            bad_hash = _make_sample_record("0" * 64)
            with self.assertRaises(ImportValidationError):
                ingest_article_record(db, bad_hash)

            # Confirm nothing partial was committed
            conn = library_schema.connect(db)
            try:
                library_schema.initialize(conn)
                self.assertEqual(library_schema.audit(conn)["articles"], 0)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
