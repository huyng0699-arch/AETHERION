"""Longitudinal query tests for Q-0035: chronological sorting and stable identifiers."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class CoreLongitudinalTests(unittest.TestCase):
    def test_chronological_sorting_across_timezones_with_stable_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "longitudinal.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_series",
                password="ops-series-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                login = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_series", "password": "ops-series-password-123"},
                )
                headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

                # Ingest out-of-order points with mixed timezone offsets:
                # Point A: 09:00+07:00 == 02:00Z (earliest)
                # Point B: 03:00+00:00 == 03:00Z (middle)
                # Point C: 11:00+07:00 == 04:00Z (latest)
                points = [
                    ("11:00:00+07:00", 78.0),
                    ("09:00:00+07:00", 62.0),
                    ("03:00:00+00:00", 70.0),
                ]
                created_ids = []
                for ts_suffix, val in points:
                    resp = client.post(
                        "/api/v1/observations",
                        headers=headers,
                        json={
                            "subject_id": "CREW-1",
                            "scope": "CREW",
                            "metric": "heart_rate",
                            "value": val,
                            "unit": "beats/min",
                            "source_id": "manual_log",
                            "observed_at": f"2026-11-14T{ts_suffix}",
                        },
                    )
                    self.assertEqual(resp.status_code, 201)
                    created_ids.append(resp.json()["observation"]["observation_uid"])

                # Longitudinal series defaults to ascending chronological order
                series = client.get(
                    "/api/v1/observations/series",
                    params={"subject_id": "CREW-1", "metric": "heart_rate"},
                    headers=headers,
                )
                self.assertEqual(series.status_code, 200)
                body = series.json()
                self.assertEqual(body["order"], "asc")
                self.assertEqual(body["count"], 3)
                self.assertEqual([p["value"] for p in body["points"]], [62.0, 70.0, 78.0])
                self.assertEqual(
                    [p["observation_uid"] for p in body["points"]],
                    [created_ids[1], created_ids[2], created_ids[0]],
                )

                # Time-window filtering
                window = client.get(
                    "/api/v1/observations/series",
                    params={
                        "subject_id": "CREW-1",
                        "metric": "heart_rate",
                        "since": "2026-11-14T02:30:00+00:00",
                        "until": "2026-11-14T03:30:00+00:00",
                    },
                    headers=headers,
                )
                self.assertEqual(window.status_code, 200)
                self.assertEqual([p["value"] for p in window.json()["points"]], [70.0])

                # Negative: invalid order rejected
                bad_order = client.get(
                    "/api/v1/observations/series",
                    params={"subject_id": "CREW-1", "metric": "heart_rate", "order": "random"},
                    headers=headers,
                )
                self.assertEqual(bad_order.status_code, 422)


if __name__ == "__main__":
    unittest.main()
