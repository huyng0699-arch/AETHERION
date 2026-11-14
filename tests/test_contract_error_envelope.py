"""Tests for Q-0021 stable error response envelope across 4xx/5xx statuses."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]


class ErrorEnvelopeContractTests(unittest.TestCase):
    def test_schema_declares_error_envelope(self) -> None:
        schema_path = ROOT / "packages" / "contracts" / "error_envelope.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["required"], ["error", "detail"])
        self.assertIn("VALIDATION_ERROR", schema["properties"]["error"]["properties"]["code"]["enum"])

    def test_401_403_404_422_and_500_return_consistent_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "errors.sqlite3"
            ensure_bootstrap_user(
                db,
                username="crew_err",
                password="crew-err-password-123",
                role="crew",
                allowed_subjects=["CREW-ERR"],
            )
            app = create_app(db_path=db)

            @app.get("/_test_boom")
            def boom():
                raise RuntimeError("boom")

            with TestClient(app, raise_server_exceptions=False) as client:
                # 401
                r401 = client.get("/api/v1/observations", params={"subject_id": "CREW-ERR"})
                self.assertEqual(r401.status_code, 401)
                self.assertEqual(r401.json()["error"]["code"], "UNAUTHORIZED")
                self.assertTrue(r401.json()["error"]["action"])

                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "crew_err", "password": "crew-err-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}"}

                # 403
                r403 = client.get("/api/v1/observations", params={"subject_id": "CREW-OTHER"}, headers=headers)
                self.assertEqual(r403.status_code, 403)
                self.assertEqual(r403.json()["error"]["code"], "FORBIDDEN")

                # 404
                r404 = client.get("/api/v1/subjects/CREW-ERR", headers=headers)
                self.assertEqual(r404.status_code, 404)
                self.assertEqual(r404.json()["error"]["code"], "NOT_FOUND")

                # 422
                r422 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={"subject_id": "CREW-ERR"},
                )
                self.assertEqual(r422.status_code, 422)
                self.assertEqual(r422.json()["error"]["code"], "VALIDATION_ERROR")

                # 500
                r500 = client.get("/_test_boom")
                self.assertEqual(r500.status_code, 500)
                self.assertEqual(r500.json()["error"]["code"], "INTERNAL_ERROR")
                self.assertTrue(r500.json()["error"]["action"])


if __name__ == "__main__":
    unittest.main()
