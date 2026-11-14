"""Focused verification for Q-0448: pack verified CliFF JSON library into offline SQLite."""

import json
from pathlib import Path
import tempfile
import unittest

from knowledge.nasa.cliff_119_2023 import importer, library_schema

REPO_ROOT = Path(__file__).resolve().parents[1]
RECORDS_DIR = REPO_ROOT / "knowledge" / "nasa" / "cliff_119_2023" / "records"


class OfflineLibraryPackTests(unittest.TestCase):
    def test_pack_preserves_full_content_and_reports_missing_originals(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / library_schema.DEFAULT_LIBRARY_NAME
            result = importer.pack_offline_library(
                db_path=db_path,
                records_dir=RECORDS_DIR,
                assets_root=REPO_ROOT,
            )
            audit = result["audit"]
            self.assertEqual(audit["integrity"], "ok")
            self.assertEqual(audit["foreign_key_errors"], 0)
            self.assertEqual(audit["media_hash_mismatches"], [])
            self.assertGreaterEqual(len(result["ingested_articles"]), 116)
            self.assertEqual(audit["articles"], len(result["ingested_articles"]))
            self.assertIn("CLIFF-119", result["missing_originals"])
            self.assertFalse(audit["library_complete"])

            # Verify no shortening of sections, tables, references, or images for sample records
            conn = library_schema.connect(db_path, read_only=True)
            try:
                for cid in ("CLIFF-001", "CLIFF-066"):
                    raw = json.loads((RECORDS_DIR / f"{cid}.json").read_text(encoding="utf-8"))
                    sec_count = conn.execute(
                        "SELECT COUNT(*) FROM article_sections WHERE article_id = ?", (cid,)
                    ).fetchone()[0]
                    tbl_count = conn.execute(
                        "SELECT COUNT(*) FROM article_tables WHERE article_id = ?", (cid,)
                    ).fetchone()[0]
                    ref_count = conn.execute(
                        "SELECT COUNT(*) FROM source_references WHERE article_id = ?", (cid,)
                    ).fetchone()[0]
                    med_count = conn.execute(
                        "SELECT COUNT(*) FROM media WHERE article_id = ?", (cid,)
                    ).fetchone()[0]
                    self.assertEqual(sec_count, len(raw.get("sections", [])))
                    self.assertEqual(tbl_count, len(raw.get("tables", [])))
                    self.assertEqual(ref_count, len(raw.get("references", [])))
                    self.assertEqual(med_count, len(raw.get("media", [])))
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
