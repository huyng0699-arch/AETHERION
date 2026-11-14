"""E2E test for Q-0249: Offline application works with Internet and model service disabled."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.request

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
for p in (str(REPO_ROOT), str(SERVER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from aetherion_server.care.episode import CareEpisodeStore  # noqa: E402
from aetherion_server.main import create_app  # noqa: E402


def _block_network(*args, **kwargs):
    raise OSError("Network disabled for offline E2E test")


class OfflineApplicationE2ETests(unittest.TestCase):
    def test_local_api_knowledge_and_interview_work_with_internet_and_ai_disabled(self) -> None:
        old_env = {
            k: os.environ.get(k)
            for k in (
                "AETHERION_BOOTSTRAP_USER",
                "AETHERION_BOOTSTRAP_PASSWORD",
                "AETHERION_BOOTSTRAP_ROLE",
                "AETHERION_INTERVIEW_AI_PROVIDER",
            )
        }
        os.environ["AETHERION_BOOTSTRAP_USER"] = "offline_ops"
        os.environ["AETHERION_BOOTSTRAP_PASSWORD"] = "offline-password-123"
        os.environ["AETHERION_BOOTSTRAP_ROLE"] = "operator"
        os.environ["AETHERION_INTERVIEW_AI_PROVIDER"] = "disabled"
        try:
            with patch.object(urllib.request, "urlopen", side_effect=_block_network):
                with tempfile.TemporaryDirectory() as tmpdir:
                    db_path = Path(tmpdir) / "offline.sqlite3"
                    app = create_app(db_path=db_path)
                    with TestClient(app) as client:
                        # 1. Health & readiness
                        self.assertEqual(client.get("/health").status_code, 200)
                        self.assertEqual(client.get("/ready").status_code, 200)

                        # 2. Local auth + observation write/readback
                        login = client.post(
                            "/api/v1/auth/login",
                            json={"username": "offline_ops", "password": "offline-password-123"},
                        )
                        self.assertEqual(login.status_code, 200)
                        token = login.json()["access_token"]
                        post_obs = client.post(
                            "/api/v1/observations",
                            headers={"Authorization": f"Bearer {token}"},
                            json={
                                "subject_id": "CREW-01",
                                "scope": "CREW",
                                "metric": "heart_rate",
                                "value": 68.0,
                                "unit": "beats/min",
                                "source_id": "local_pulse_ox",
                                "observed_at": "2026-11-14T10:20:00+00:00",
                                "quality": "READY",
                                "verification_state": "SELF_REPORTED",
                            },
                        )
                        self.assertEqual(post_obs.status_code, 201)
                        get_obs = client.get(
                            "/api/v1/observations",
                            params={"subject_id": "CREW-01"},
                            headers={"Authorization": f"Bearer {token}"},
                        )
                        self.assertEqual(get_obs.status_code, 200)
                        self.assertEqual(len(get_obs.json()["observations"]), 1)

                        # 3. Local NASA CliFF search & readback without network
                        kb = client.get("/api/v1/knowledge/articles", params={"query": "seizure", "limit": 5})
                        self.assertEqual(kb.status_code, 200)
                        self.assertGreaterEqual(kb.json()["matched"], 1)

                        # 4. Deterministic interview continues when AI is disabled
                        ai_st = client.get("/api/v1/knowledge/interview/ai-status")
                        self.assertEqual(ai_st.status_code, 200)
                        self.assertFalse(ai_st.json()["configured"])

                        sym = client.get("/api/v1/knowledge/symptoms", params={"query": "sot", "limit": 3})
                        self.assertEqual(sym.status_code, 200)
                        first_sym = sym.json()["items"][0]["name"]

                        iv = client.post(
                            "/api/v1/knowledge/interview/next",
                            json={"symptoms": [first_sym], "answers": {}, "use_ai": False},
                        )
                        self.assertEqual(iv.status_code, 200)
                        self.assertEqual(iv.json()["model_status"], "NOT_REQUESTED")
                        self.assertIsNotNone(iv.json()["next_question"])

                    # 5. Local CareEpisodeStore works offline
                    care = CareEpisodeStore(Path(tmpdir) / "care.sqlite")
                    ep = care.start_episode(
                        subject_id="CREW-01",
                        actor_id="offline_ops",
                        chief_concern="Fever check",
                        source="offline_intake",
                        recorded_at="2026-11-14T10:20:00+00:00",
                    )
                    self.assertEqual(ep["current_phase"], "GATHER")
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
