"""Input validation tests for Q-0048 POST /api/v1/observations."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class ServerObservationsPostValidationTests(unittest.TestCase):
    def test_rejects_malformed_and_out_of_range_inputs_with_typed_422(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "post_val.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_post",
                password="ops-post-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_post", "password": "ops-post-password-123"},
                ).json()["access_token"]
                headers = {"Authorization": f"Bearer {tok}"}

                # Malformed JSON -> 422 typed error detail
                malformed = client.post(
                    "/api/v1/observations",
                    headers={**headers, "Content-Type": "application/json"},
                    content="{not-valid-json",
                )
                self.assertEqual(malformed.status_code, 422)
                self.assertIn("detail", malformed.json())

                # Out-of-range SpO2 (> 100%) -> 422 typed error
                bad_spo2 = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "spo2",
                        "value": 150.0,
                        "unit": "%",
                        "source_id": "manual",
                        "observed_at": "2026-11-14T05:00:00+00:00",
                    },
                )
                self.assertEqual(bad_spo2.status_code, 422)
                self.assertIsInstance(bad_spo2.json()["detail"], list)

                # Negative heart rate -> 422 typed error
                bad_hr = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": -5.0,
                        "unit": "beats/min",
                        "source_id": "manual",
                        "observed_at": "2026-11-14T05:00:00+00:00",
                    },
                )
                self.assertEqual(bad_hr.status_code, 422)

                # Valid in-range input -> 201
                ok = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "spo2",
                        "value": 98.0,
                        "unit": "%",
                        "source_id": "manual",
                        "observed_at": "2026-11-14T05:00:00+00:00",
                    },
                )
                self.assertEqual(ok.status_code, 201)


if __name__ == "__main__":
    unittest.main()
