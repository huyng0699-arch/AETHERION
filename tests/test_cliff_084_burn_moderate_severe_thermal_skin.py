"""Tests for CLIFF-084 Burn Moderate-Severe Thermal Skin provenance, media, and SQLite ingestion (Q-0384)."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from knowledge.nasa.cliff_119_2023 import importer

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "records" / "CLIFF-084.json"
QA_PATH = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "qa" / "CLIFF-084.json"


class TestCliff084BurnModerateSevereThermalSkin(unittest.TestCase):
    def test_record_and_qa_exist_with_nasa_provenance(self) -> None:
        self.assertTrue(RECORD_PATH.is_file())
        self.assertTrue(QA_PATH.is_file())
        record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        qa = json.loads(QA_PATH.read_text(encoding="utf-8"))

        self.assertEqual(record["article_id"], "CLIFF-084")
        self.assertEqual(record["slot"], 84)
        self.assertEqual(record["source"]["publisher"], "NASA")
        self.assertIn("burn-moderate-to-severe-thermal-cliff-2023.pdf", record["source"]["source_url"])
        self.assertEqual(len(record["sections"]), 14)
        self.assertGreaterEqual(len(record["media"]), 3)
        self.assertTrue(qa["safety_disclaimer_present"])

        for media in record["media"]:
            asset = REPO_ROOT / media["file_path"]
            self.assertTrue(asset.is_file(), f"Missing asset {asset}")
            raw = asset.read_bytes()
            self.assertGreater(len(raw), 0)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), media["sha256"])

    def test_sqlite_ingestion_and_blob_readback(self) -> None:
        record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cliff_test.sqlite"
            res = importer.ingest_article_record(db_path, record, assets_root=REPO_ROOT)
            self.assertEqual(res["article_id"], "CLIFF-084")

            conn = sqlite3.connect(db_path)
            try:
                sec_count = conn.execute("SELECT count(*) FROM article_sections WHERE article_id = ?", ("CLIFF-084",)).fetchone()[0]
                self.assertEqual(sec_count, 14)
                blobs = conn.execute("SELECT media_id, length(data), sha256 FROM media WHERE article_id = ?", ("CLIFF-084",)).fetchall()
                self.assertEqual(len(blobs), 3)
            finally:
                conn.close()

    def test_negative_tampered_media_hash_rejected(self) -> None:
        record = copy.deepcopy(json.loads(RECORD_PATH.read_text(encoding="utf-8")))
        record["media"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "cliff_bad.sqlite"
            with self.assertRaises(importer.ImportValidationError):
                importer.ingest_article_record(db_path, record, assets_root=REPO_ROOT)


if __name__ == "__main__":
    unittest.main()
