"""Negative and positive validation tests for Q-0033 (NaN, Inf, units, naive time)."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class CoreValidationTests(unittest.TestCase):
    def test_rejects_nan_inf_incompatible_units_and_naive_time(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "validation.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_val",
                password="ops-val-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_val", "password": "ops-val-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                # NaN rejected
                nan_resp = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    content=(
                        '{"subject_id":"CREW-1","metric":"heart_rate","value":NaN,'
                        '"unit":"beats/min","source_id":"manual","observed_at":"2026-11-14T04:55:00+00:00"}'
                    ),
                )
                self.assertEqual(nan_resp.status_code, 422)

                # +Inf and -Inf rejected
                for nonfinite in ("Infinity", "-Infinity"):
                    inf_resp = client.post(
                        "/api/v1/observations",
                        headers=headers,
                        content=(
                            f'{{"subject_id":"CREW-1","metric":"heart_rate","value":{nonfinite},'
                            '"unit":"beats/min","source_id":"manual","observed_at":"2026-11-14T04:55:00+00:00"}'
                        ),
                    )
                    self.assertEqual(inf_resp.status_code, 422)

                # Incompatible unit rejected (kg for heart_rate)
                bad_unit = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "kg",
                        "source_id": "manual",
                        "observed_at": "2026-11-14T04:55:00+00:00",
                    },
                )
                self.assertEqual(bad_unit.status_code, 422)

                # Timezone-free timestamp rejected
                naive_time = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "manual",
                        "observed_at": "2026-11-14T04:55:00",
                    },
                )
                self.assertEqual(naive_time.status_code, 422)

                # Valid measurement accepted
                ok = client.post(
                    "/api/v1/observations",
                    headers=headers,
                    json={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "value": 72.0,
                        "unit": "beats/min",
                        "source_id": "manual",
                        "observed_at": "2026-11-14T04:55:00+00:00",
                    },
                )
                self.assertEqual(ok.status_code, 201)


if __name__ == "__main__":
    unittest.main()
