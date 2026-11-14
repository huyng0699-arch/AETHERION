"""Retrieval and provenance verification tests for Q-0047 GET /api/v1/observations."""

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class ServerObservationsGetTests(unittest.TestCase):
    def test_get_observations_preserves_subject_and_full_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "obs_get.sqlite3"
            ensure_bootstrap_user(
                db,
                username="ops_get",
                password="ops-get-password-123",
                role="operator",
                allowed_subjects=["*"],
            )
            ensure_bootstrap_user(
                db,
                username="crew_one",
                password="crew-one-password-123",
                role="crew",
                allowed_subjects=["CREW-1"],
            )
            app = create_app(db_path=db)
            with TestClient(app) as client:
                ops_tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "ops_get", "password": "ops-get-password-123"},
                ).json()["access_token"]
                ops_h = {"Authorization": f"Bearer {ops_tok}"}

                for subj, metric, val, unit, src in (
                    ("CREW-1", "heart_rate", 68.0, "beats/min", "crew_manual"),
                    ("CREW-1", "spo2", 99.0, "%", "pulse_ox_unverified"),
                    ("CREW-2", "heart_rate", 75.0, "beats/min", "crew_manual"),
                ):
                    r = client.post(
                        "/api/v1/observations",
                        headers=ops_h,
                        json={
                            "subject_id": subj,
                            "scope": "CREW",
                            "metric": metric,
                            "value": val,
                            "unit": unit,
                            "source_id": src,
                            "observed_at": "2026-11-14T05:00:00+00:00",
                            "quality": "READY",
                            "verification_state": "SELF_REPORTED",
                        },
                    )
                    self.assertEqual(r.status_code, 201)

                # Crew user retrieves only CREW-1 and sees full provenance
                crew_tok = client.post(
                    "/api/v1/auth/login",
                    json={"username": "crew_one", "password": "crew-one-password-123"},
                ).json()["access_token"]
                crew_h = {"Authorization": f"Bearer {crew_tok}"}

                res = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-1", "metric": "spo2"},
                    headers=crew_h,
                )
                self.assertEqual(res.status_code, 200)
                obs = res.json()["observations"]
                self.assertEqual(len(obs), 1)
                row = obs[0]
                self.assertEqual(row["subject_id"], "CREW-1")
                self.assertEqual(row["metric"], "spo2")
                self.assertEqual(row["value"], 99.0)
                self.assertEqual(row["unit"], "%")
                self.assertEqual(row["source_id"], "pulse_ox_unverified")
                self.assertEqual(row["quality"], "READY")
                self.assertEqual(row["verification_state"], "SELF_REPORTED")
                self.assertTrue(row["received_at"])
                self.assertTrue(row["observation_uid"].startswith("obs-"))

                # Negative: CREW-1 user cannot retrieve CREW-2
                denied = client.get(
                    "/api/v1/observations",
                    params={"subject_id": "CREW-2"},
                    headers=crew_h,
                )
                self.assertEqual(denied.status_code, 403)


if __name__ == "__main__":
    unittest.main()
