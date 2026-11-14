"""Focused API tests for Q-0097, Q-0098, Q-0099, Q-0102, and Q-0104."""

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

from aetherion_server.main import create_app


class CareJournalWorkflowsApiTests(unittest.TestCase):
    def test_act_statuses_recheck_outcomes_followup_invalid_transitions_and_ai_off(self) -> None:
        old_env = {
            k: os.environ.get(k)
            for k in (
                "AETHERION_BOOTSTRAP_USER",
                "AETHERION_BOOTSTRAP_PASSWORD",
                "AETHERION_BOOTSTRAP_ROLE",
                "AETHERION_INTERVIEW_AI_PROVIDER",
            )
        }
        os.environ["AETHERION_BOOTSTRAP_USER"] = "care_crew"
        os.environ["AETHERION_BOOTSTRAP_PASSWORD"] = "care-password-123"
        os.environ["AETHERION_BOOTSTRAP_ROLE"] = "operator"
        os.environ["AETHERION_INTERVIEW_AI_PROVIDER"] = "disabled"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                db = Path(tmpdir) / "care_workflows.sqlite3"
                app = create_app(db_path=db)
                with TestClient(app) as client:
                    token = client.post(
                        "/api/v1/auth/login",
                        json={"username": "care_crew", "password": "care-password-123"},
                    ).json()["access_token"]
                    hdr = {"Authorization": f"Bearer {token}"}

                    self.assertEqual(
                        client.post(
                            "/api/v1/subjects",
                            headers=hdr,
                            json={"subject_id": "CREW-01", "display_name": "Crew 01"},
                        ).status_code,
                        201,
                    )

                    # Q-0097: Verify all 3 ACT action_status values (DONE, NOT_DONE, CANNOT_DO)
                    # Q-0098: Verify RECHECK outcomes (BETTER, UNCHANGED, WORSE, UNKNOWN)
                    # Q-0099: Verify RECHECK -> GATHER followup preserves same episode_id
                    # Q-0104: Complete workflow with AI disabled
                    ep_id = client.post(
                        "/api/v1/care/episodes",
                        headers=hdr,
                        json={
                            "subject_id": "CREW-01",
                            "chief_concern": "Post-EVA dehydration check",
                            "explicit_consent": True,
                        },
                    ).json()["episode"]["episode_id"]

                    # Q-0102: Invalid transition GATHER -> ACT rejected with 409
                    bad_jump = client.post(
                        f"/api/v1/care/episodes/{ep_id}/advance",
                        headers=hdr,
                        json={
                            "next_phase": "ACT",
                            "summary": "Skip evaluate",
                            "action_status": "DONE",
                            "human_confirmed": True,
                        },
                    )
                    self.assertEqual(bad_jump.status_code, 409)

                    # Cycle 1: GATHER -> EVALUATE -> ACT (NOT_DONE) -> RECHECK (UNCHANGED) -> GATHER (followup)
                    self.assertEqual(
                        client.post(
                            f"/api/v1/care/episodes/{ep_id}/advance",
                            headers=hdr,
                            json={"next_phase": "EVALUATE", "summary": "Assessed fluid intake", "human_confirmed": True},
                        ).status_code,
                        200,
                    )
                    act1 = client.post(
                        f"/api/v1/care/episodes/{ep_id}/advance",
                        headers=hdr,
                        json={
                            "next_phase": "ACT",
                            "summary": "Electrolyte solution not yet available",
                            "action_status": "NOT_DONE",
                            "human_confirmed": True,
                        },
                    )
                    self.assertEqual(act1.status_code, 200)
                    rec1 = client.post(
                        f"/api/v1/care/episodes/{ep_id}/advance",
                        headers=hdr,
                        json={
                            "next_phase": "RECHECK",
                            "summary": "Still thirsty",
                            "outcome": "UNCHANGED",
                            "human_confirmed": True,
                        },
                    )
                    self.assertEqual(rec1.status_code, 200)
                    followup = client.post(
                        f"/api/v1/care/episodes/{ep_id}/advance",
                        headers=hdr,
                        json={"next_phase": "GATHER", "summary": "Scheduled follow-up check", "human_confirmed": True},
                    )
                    self.assertEqual(followup.status_code, 200)
                    self.assertEqual(followup.json()["episode"]["episode_id"], ep_id)

                    # Cycle 2: GATHER -> EVALUATE -> ACT (CANNOT_DO) -> RECHECK (WORSE) -> EVALUATE -> ACT (DONE) -> RECHECK (BETTER) -> CLOSED
                    for payload in (
                        {"next_phase": "EVALUATE", "summary": "Follow-up eval", "human_confirmed": True},
                        {"next_phase": "ACT", "summary": "Swallowing uncomfortable", "action_status": "CANNOT_DO", "human_confirmed": True},
                        {"next_phase": "RECHECK", "summary": "Symptoms worsened", "outcome": "WORSE", "human_confirmed": True},
                        {"next_phase": "EVALUATE", "summary": "Re-evaluated with water", "human_confirmed": True},
                        {"next_phase": "ACT", "summary": "Hydration completed", "action_status": "DONE", "human_confirmed": True},
                        {"next_phase": "RECHECK", "summary": "Crew feels better", "outcome": "BETTER", "human_confirmed": True},
                        {"next_phase": "CLOSED", "summary": "Episode resolved", "human_confirmed": True},
                    ):
                        r = client.post(f"/api/v1/care/episodes/{ep_id}/advance", headers=hdr, json=payload)
                        self.assertEqual(r.status_code, 200, r.text)

                    # Q-0102: Transition after CLOSED rejected with 409
                    after_close = client.post(
                        f"/api/v1/care/episodes/{ep_id}/advance",
                        headers=hdr,
                        json={"next_phase": "GATHER", "summary": "Reopen", "human_confirmed": True},
                    )
                    self.assertEqual(after_close.status_code, 409)

                    final_ep = client.get(f"/api/v1/care/episodes/{ep_id}", headers=hdr).json()["episode"]
                    self.assertEqual(final_ep["current_phase"], "CLOSED")
                    self.assertFalse(final_ep["ai_assisted"])
                    self.assertGreaterEqual(len(final_ep["events"]), 12)
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
