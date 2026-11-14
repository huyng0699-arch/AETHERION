"""Contract and live API behavioral tests for Q-0017 crew/subject identity."""

import json
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app

ROOT = Path(__file__).resolve().parents[1]


class SubjectIdentityContractTests(unittest.TestCase):
    def test_schema_forbids_fallback_and_blank_subject(self) -> None:
        schema_path = ROOT / "packages" / "contracts" / "subject_identity.schema.json"
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["allow_fallback"]["const"], False)
        self.assertEqual(schema["x-aetherion-policy"]["fallback_to_default_crew"], False)
        self.assertEqual(schema["properties"]["subject_id"]["minLength"], 1)

    def test_api_rejects_missing_blank_and_wrong_subject_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "subject_contract.sqlite3"
            ensure_bootstrap_user(
                db,
                username="crew_a",
                password="crew-a-password-123",
                role="crew",
                allowed_subjects=["CREW-A"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "crew_a", "password": "crew-a-password-123"},
                )
                self.assertEqual(login.status_code, 200)
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                # Missing subject_id on GET -> 422, never falls back to CREW-A
                missing_get = client.get("/api/v1/observations", headers=headers)
                self.assertEqual(missing_get.status_code, 422)

                # Blank subject_id on GET -> 422
                blank_get = client.get("/api/v1/observations", params={"subject_id": ""}, headers=headers)
                self.assertEqual(blank_get.status_code, 422)

                # Wrong/unauthorized subject_id on GET and POST -> 403, never falls back
                wrong_get = client.get("/api/v1/observations", params={"subject_id": "CREW-B"}, headers=headers)
                self.assertEqual(wrong_get.status_code, 403)

                wrong_post = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-B",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "manual_entry",
                        "observed_at": "2026-11-14T04:50:00+00:00",
                    },
                )
                self.assertEqual(wrong_post.status_code, 403)


if __name__ == "__main__":
    unittest.main()
