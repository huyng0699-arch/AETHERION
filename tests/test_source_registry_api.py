"""Focused API verification test for Q-0052: source registry API."""

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


class SourceRegistryApiTests(unittest.TestCase):
    def test_resolve_recorded_source_to_license_uri_and_verification_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = create_app(db_path=Path(tmpdir) / "sources.sqlite3")
            with TestClient(app) as client:
                list_resp = client.get("/api/v1/sources", params={"limit": 50})
                self.assertEqual(list_resp.status_code, 200)
                data = list_resp.json()
                self.assertGreaterEqual(data["total"], 100)
                first_id = data["items"][0]["source_id"]

                detail_resp = client.get(f"/api/v1/sources/{first_id}")
                self.assertEqual(detail_resp.status_code, 200)
                detail = detail_resp.json()
                self.assertEqual(detail["source_id"], first_id)
                self.assertTrue(detail["license"])
                self.assertTrue(detail["source_uri"])
                self.assertTrue(detail["verification_status"])

                # Also verify ASTRA symptom vocabulary source
                sym_resp = client.get("/api/v1/sources/astra-symptom-vocabulary-819")
                self.assertEqual(sym_resp.status_code, 200)
                self.assertEqual(sym_resp.json()["verification_status"], "UNREVIEWED_VOCABULARY_ONLY")

                # Negative test: unknown source_id -> 404
                missing = client.get("/api/v1/sources/nonexistent-source-xyz")
                self.assertEqual(missing.status_code, 404)


if __name__ == "__main__":
    unittest.main()
