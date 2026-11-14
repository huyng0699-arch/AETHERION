import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIFF_DIR = ROOT / "knowledge" / "nasa" / "cliff_119_2023"
sys.path.insert(0, str(ROOT / "scripts"))
import medical_image_rights as mir  # noqa: E402


def _load_importer():
    spec = importlib.util.spec_from_file_location("cliff_importer", CLIFF_DIR / "importer.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class TestQ0457MissingCliffRecords(unittest.TestCase):
    def test_cliff_019_and_021_records_media_and_sqlite_import(self):
        importer = _load_importer()
        for cid, expected_pages in [("CLIFF-019", 15), ("CLIFF-021", 13)]:
            rec_path = CLIFF_DIR / "records" / f"{cid}.json"
            qa_path = CLIFF_DIR / "qa" / f"{cid}.json"
            self.assertTrue(rec_path.exists(), f"Missing {rec_path}")
            self.assertTrue(qa_path.exists(), f"Missing {qa_path}")

            rec = json.loads(rec_path.read_text(encoding="utf-8"))
            qa = json.loads(qa_path.read_text(encoding="utf-8"))

            self.assertEqual(rec["article_id"], cid)
            self.assertEqual(rec["completeness_state"], "COMPLETE")
            self.assertEqual(rec["source"]["verification_state"], "VERIFIED")
            self.assertEqual(len(rec["sections"]), expected_pages)
            self.assertGreaterEqual(len(rec["media"]), 3)
            self.assertEqual(qa["pdf_sha256"], rec["source"]["content_sha256"])
            self.assertEqual(qa["media_count"], len(rec["media"]))

            for m in rec["media"]:
                img_path = ROOT / m["file_path"]
                self.assertTrue(img_path.exists(), f"Missing image {img_path}")
                img_bytes = img_path.read_bytes()
                self.assertEqual(hashlib.sha256(img_bytes).hexdigest(), m["sha256"])
                mir.verify_image(img_bytes, m["mime_type"])
                sidecar = json.loads((img_path.parent / f"{img_path.name}.json").read_text(encoding="utf-8"))
                mir.verify_metadata(sidecar)

        import sqlite3
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test_cliff.sqlite"
            for cid in ["CLIFF-019", "CLIFF-021"]:
                rec = json.loads((CLIFF_DIR / "records" / f"{cid}.json").read_text(encoding="utf-8"))
                importer.ingest_article_record(db_path, rec, assets_root=ROOT)
            conn = sqlite3.connect(db_path)
            try:
                rows = conn.execute(
                    "SELECT article_id, display_title FROM articles WHERE article_id IN ('CLIFF-019','CLIFF-021') ORDER BY article_id"
                ).fetchall()
                self.assertEqual([r[0] for r in rows], ["CLIFF-019", "CLIFF-021"])
                media_cnt = conn.execute(
                    "SELECT COUNT(*) FROM media WHERE article_id IN ('CLIFF-019','CLIFF-021') AND length(data) > 0"
                ).fetchone()[0]
                self.assertEqual(media_cnt, 6)
            finally:
                conn.close()

    def test_cliff_119_remains_unresolved_and_not_fabricated(self):
        self.assertFalse((CLIFF_DIR / "records" / "CLIFF-119.json").exists())
        qa119 = json.loads((CLIFF_DIR / "qa" / "CLIFF-119.json").read_text(encoding="utf-8"))
        self.assertEqual(qa119["review_status"], "BLOCKED_SOURCE_UNRESOLVED")
        self.assertFalse(qa119["audit"]["official_unique_119th_identified"])
        self.assertEqual(qa119["audit"]["nasa_imm_cliff119_published_rows"], 118)
        self.assertIn("CLIFF-019", qa119["audit"]["distinction_from_019_and_021"])


if __name__ == "__main__":
    unittest.main()
