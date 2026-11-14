"""Focused API verification test for Q-0058: scientific reference search API."""

from __future__ import annotations

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


class ScientificReferenceSearchApiTests(unittest.TestCase):
    def test_search_curated_entries_with_verification_labels_and_negative_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = create_app(db_path=Path(tmpdir) / "sci_search.sqlite3")
            with TestClient(app) as client:
                r = client.get("/api/v1/knowledge/articles", params={"query": "seizure", "limit": 10})
                self.assertEqual(r.status_code, 200)
                body = r.json()
                self.assertGreaterEqual(body["matched"], 1)
                first = body["items"][0]
                self.assertIn("source_claim", first)
                self.assertIn("content_state", first)
                self.assertTrue(first["original_url"])

                # Negative: non-existent term returns 0 matches (no fabricated entries)
                empty = client.get("/api/v1/knowledge/articles", params={"query": "zzz_nonexistent_xyz_999"})
                self.assertEqual(empty.status_code, 200)
                self.assertEqual(empty.json()["matched"], 0)
                self.assertEqual(empty.json()["items"], [])

                # Negative: unknown article_id returns 404
                missing = client.get("/api/v1/knowledge/articles/CLIFF-999")
                self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
