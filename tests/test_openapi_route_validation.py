"""Focused API verification test for Q-0060: OpenAPI schema and 4xx error response envelopes."""

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


class OpenApiRouteValidationTests(unittest.TestCase):
    def test_openapi_schema_and_error_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            app = create_app(db_path=Path(tmpdir) / "openapi.sqlite3")
            schema = app.openapi()
            self.assertTrue(str(schema.get("openapi", "")).startswith("3."))
            paths = schema.get("paths", {})
            for expected_path in (
                "/health",
                "/ready",
                "/api/v1/auth/login",
                "/api/v1/observations",
                "/api/v1/sources",
                "/api/v1/knowledge/articles",
                "/api/v1/care/episodes",
            ):
                self.assertIn(expected_path, paths, f"Missing {expected_path} in OpenAPI schema")

            with TestClient(app) as client:
                # 401 envelope
                r401 = client.get("/api/v1/observations", params={"subject_id": "CREW-01"})
                self.assertEqual(r401.status_code, 401)
                e401 = r401.json()["error"]
                self.assertEqual(e401["code"], "UNAUTHORIZED")
                self.assertEqual(e401["status"], 401)

                # 404 envelope
                r404 = client.get("/api/v1/sources/unknown-source-id")
                self.assertEqual(r404.status_code, 404)
                e404 = r404.json()["error"]
                self.assertEqual(e404["code"], "NOT_FOUND")
                self.assertEqual(e404["status"], 404)

                # 422 envelope
                r422 = client.post("/api/v1/auth/login", json={"username": "", "password": ""})
                self.assertEqual(r422.status_code, 422)
                e422 = r422.json()["error"]
                self.assertEqual(e422["code"], "VALIDATION_ERROR")
                self.assertEqual(e422["status"], 422)


if __name__ == "__main__":
    unittest.main()
