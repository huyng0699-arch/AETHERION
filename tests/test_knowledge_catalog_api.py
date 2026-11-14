from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.main import create_app


class KnowledgeCatalogApiTests(unittest.TestCase):
    def test_cliff_json_indexing_search_and_missing_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "knowledge.sqlite3"
            app = create_app(db_path=db_path)
            with TestClient(app) as client:
                status_resp = client.get("/api/v1/knowledge/status")
                self.assertEqual(status_resp.status_code, 200)
                st = status_resp.json()
                self.assertGreaterEqual(st["json_articles"], 116)
                self.assertEqual(st["expected_slots"], 119)
                self.assertIn("CLIFF-119", st["missing_slots"])
                self.assertFalse(st["original_pdf_archive_verified"])
                self.assertTrue(st["article_full_text_search"])

                # Full-text search
                search_resp = client.get("/api/v1/knowledge/articles", params={"query": "seizure", "limit": 10})
                self.assertEqual(search_resp.status_code, 200)
                search_data = search_resp.json()
                self.assertGreaterEqual(search_data["matched"], 1)
                ids = [item["article_id"] for item in search_data["items"]]
                self.assertIn("CLIFF-061", ids)
                cliff_061_summary = next(item for item in search_data["items"] if item["article_id"] == "CLIFF-061")
                self.assertGreater(cliff_061_summary["text_words"], 0)
                self.assertTrue(cliff_061_summary["original_url"])
                self.assertEqual(
                    cliff_061_summary["content_state"],
                    "STRUCTURED_JSON_LOCAL_NOT_PDF_INTEGRITY_PROOF",
                )

                # Detail endpoint
                detail_resp = client.get("/api/v1/knowledge/articles/CLIFF-061")
                self.assertEqual(detail_resp.status_code, 200)
                detail = detail_resp.json()
                self.assertTrue(detail["read_only"])
                self.assertFalse(detail["clinical_decision_support"])
                self.assertGreater(len(detail["sections"]), 0)

                # Missing slot returns 404
                missing_resp = client.get("/api/v1/knowledge/articles/CLIFF-119")
                self.assertEqual(missing_resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
