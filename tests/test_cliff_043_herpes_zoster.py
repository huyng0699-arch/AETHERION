"""End-to-end verification test for Q-0343 (CLIFF-043 Herpes Zoster Reactivation (Shingles))."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from knowledge.nasa.cliff_119_2023 import importer
from packages.medical_library.rights_gate import validate_nasa_original_rights
from scripts.medical_image_rights import verify_image, verify_metadata

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = REPO_ROOT / "knowledge/nasa/cliff_119_2023/records/CLIFF-043.json"
QA_PATH = REPO_ROOT / "knowledge/nasa/cliff_119_2023/qa/CLIFF-043.json"
MEDIA_DIR = REPO_ROOT / "knowledge/nasa/cliff_119_2023/media/CLIFF-043"


class Cliff043HerpesZosterTests(unittest.TestCase):
    def test_record_provenance_sections_tables_and_media_rights(self) -> None:
        record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        qa = json.loads(QA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(record["article_id"], "CLIFF-043")
        self.assertEqual(record["slot"], 43)
        self.assertEqual(record["display_title"], "Herpes Zoster Reactivation (Shingles)")
        self.assertEqual(record["source"]["verification_state"], "VERIFIED")
        self.assertIn("risk-planning", record["source_notes"].lower())

        self.assertEqual(len(record["sections"]), 13)
        self.assertGreaterEqual(len(record["tables"]), 3)
        self.assertGreaterEqual(len(record["references"]), 10)
        self.assertGreaterEqual(len(record["media"]), 3)
        self.assertEqual(qa["media_count"], len(record["media"]))
        self.assertEqual(qa["missing_items"], [])

        audit = validate_nasa_original_rights(
            {
                "entity_id": record["article_id"],
                "entity_type": "article",
                "source_url": record["source"]["final_url"],
                "publisher": record["source"]["publisher"],
                "sha256": record["source"]["content_sha256"],
                "retrieved_at_utc": record["source"]["retrieved_at_utc"],
                "license_name": record["source"]["license_identifier"],
                "credit_line": record["source"]["attribution"],
            }
        )
        self.assertTrue(audit.redistribution_allowed)

        for media_item in record["media"]:
            asset_path = REPO_ROOT / media_item["file_path"]
            self.assertTrue(asset_path.is_file(), f"Missing asset {asset_path}")
            raw_bytes = asset_path.read_bytes()
            verified = verify_image(raw_bytes, media_item["mime_type"])
            self.assertEqual(verified["sha256"], media_item["sha256"])
            self.assertEqual(verified["width"], media_item["width"])
            self.assertEqual(verified["height"], media_item["height"])

            sidecar = MEDIA_DIR / f"{media_item['sha256']}.json"
            self.assertTrue(sidecar.is_file(), f"Missing sidecar {sidecar}")
            verify_metadata(json.loads(sidecar.read_text(encoding="utf-8")))

    def test_sqlite_idempotent_import_and_negative_hash(self) -> None:
        record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_cliff043.sqlite"
            importer.ingest_article_record(db_path, record, assets_root=REPO_ROOT)
            importer.ingest_article_record(db_path, record, assets_root=REPO_ROOT)

            conn = sqlite3.connect(db_path)
            try:
                articles = conn.execute("SELECT COUNT(*) FROM articles WHERE article_id='CLIFF-043'").fetchone()[0]
                self.assertEqual(articles, 1)

                media_rows = conn.execute("SELECT length(data), mime_type FROM media WHERE article_id='CLIFF-043'").fetchall()
                self.assertEqual(len(media_rows), len(record["media"]))
                for blob_len, _ in media_rows:
                    self.assertGreater(blob_len, 1000)

                hits = conn.execute(
                    "SELECT article_id FROM article_sections WHERE lower(text_content) LIKE '%herpes zoster%'"
                ).fetchall()
                self.assertGreaterEqual(len(hits), 1)
                self.assertEqual(hits[0][0], "CLIFF-043")
            finally:
                conn.close()

            bad_record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
            bad_record["media"][0]["sha256"] = "0" * 64
            with self.assertRaises(importer.ImportValidationError):
                importer.ingest_article_record(db_path, bad_record, assets_root=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
