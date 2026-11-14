"""Focused API verification test for Q-0054: care action/recheck transitions, invalid order, and subject mismatch."""

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

from aetherion_server.bootstrap import ensure_bootstrap_user  # noqa: E402
from aetherion_server.main import create_app  # noqa: E402
from aetherion_server.store import initialize  # noqa: E402


class CareActionRecheckApiTests(unittest.TestCase):
    def test_care_transitions_reject_invalid_order_and_subject_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "care_api.sqlite3"
            initialize(db_path)
            ensure_bootstrap_user(
                db_path,
                username="crew1_user",
                password="crew1-password-123",
                role="crew",
                allowed_subjects=["CREW-01"],
            )
            ensure_bootstrap_user(
                db_path,
                username="crew2_user",
                password="crew2-password-123",
                role="crew",
                allowed_subjects=["CREW-02"],
            )

            app = create_app(db_path=db_path)
            with TestClient(app) as client:
                t1 = client.post(
                    "/api/v1/auth/login",
                    json={"username": "crew1_user", "password": "crew1-password-123"},
                ).json()["access_token"]
                t2 = client.post(
                    "/api/v1/auth/login",
                    json={"username": "crew2_user", "password": "crew2-password-123"},
                ).json()["access_token"]
                h1 = {"Authorization": f"Bearer {t1}"}
                h2 = {"Authorization": f"Bearer {t2}"}

                # Register subject CREW-01
                reg = client.post(
                    "/api/v1/subjects",
                    headers=h1,
                    json={"subject_id": "CREW-01", "display_name": "Crew 01", "scope": "CREW"},
                )
                self.assertEqual(reg.status_code, 201, reg.text)

                # Start episode
                start = client.post(
                    "/api/v1/care/episodes",
                    headers=h1,
                    json={
                        "subject_id": "CREW-01",
                        "chief_concern": "Mild headache",
                        "symptom_terms": ["Dau dau"],
                        "explicit_consent": True,
                    },
                )
                self.assertEqual(start.status_code, 201, start.text)
                ep_id = start.json()["episode"]["episode_id"]

                # Negative: invalid skip GATHER -> ACT returns 409
                bad_order = client.post(
                    f"/api/v1/care/episodes/{ep_id}/advance",
                    headers=h1,
                    json={
                        "next_phase": "ACT",
                        "summary": "Skip evaluate",
                        "action_status": "DONE",
                        "human_confirmed": True,
                    },
                )
                self.assertEqual(bad_order.status_code, 409)

                # Negative: subject mismatch (crew2_user cannot advance CREW-01 episode) -> 404
                mismatch = client.post(
                    f"/api/v1/care/episodes/{ep_id}/advance",
                    headers=h2,
                    json={
                        "next_phase": "EVALUATE",
                        "summary": "Unauthorized access",
                        "human_confirmed": True,
                    },
                )
                self.assertEqual(mismatch.status_code, 404)

                # Valid transitions: GATHER -> EVALUATE -> ACT -> RECHECK
                ev = client.post(
                    f"/api/v1/care/episodes/{ep_id}/advance",
                    headers=h1,
                    json={"next_phase": "EVALUATE", "summary": "Reviewed hydration", "human_confirmed": True},
                )
                self.assertEqual(ev.status_code, 200, ev.text)

                act = client.post(
                    f"/api/v1/care/episodes/{ep_id}/advance",
                    headers=h1,
                    json={
                        "next_phase": "ACT",
                        "summary": "Drank 500ml water and rested",
                        "action_status": "DONE",
                        "human_confirmed": True,
                    },
                )
                self.assertEqual(act.status_code, 200, act.text)

                rec = client.post(
                    f"/api/v1/care/episodes/{ep_id}/advance",
                    headers=h1,
                    json={
                        "next_phase": "RECHECK",
                        "summary": "Headache improved",
                        "outcome": "BETTER",
                        "human_confirmed": True,
                    },
                )
                self.assertEqual(rec.status_code, 200, rec.text)
                self.assertEqual(rec.json()["episode"]["current_phase"], "RECHECK")


if __name__ == "__main__":
    unittest.main()
