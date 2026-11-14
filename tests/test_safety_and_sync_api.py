"""Focused API tests for Q-0055, Q-0056, Q-0057, and Q-0059."""

from __future__ import annotations

from datetime import datetime, timezone
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


class SafetyAndSyncApiTests(unittest.TestCase):
    def test_incident_reporting_idempotent_ack_device_heartbeat_and_sync_status(self) -> None:
        old_env = {
            k: os.environ.get(k)
            for k in ("AETHERION_BOOTSTRAP_USER", "AETHERION_BOOTSTRAP_PASSWORD", "AETHERION_BOOTSTRAP_ROLE")
        }
        os.environ["AETHERION_BOOTSTRAP_USER"] = "safety_ops"
        os.environ["AETHERION_BOOTSTRAP_PASSWORD"] = "safety-password-123"
        os.environ["AETHERION_BOOTSTRAP_ROLE"] = "operator"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                app = create_app(db_path=Path(tmpdir) / "safety_sync.sqlite3")
                with TestClient(app) as client:
                    token = client.post(
                        "/api/v1/auth/login",
                        json={"username": "safety_ops", "password": "safety-password-123"},
                    ).json()["access_token"]
                    headers = {"Authorization": f"Bearer {token}"}

                    # Q-0055 negative: WITNESS_REPORTED_UNCONSCIOUS without witness_id -> 422
                    bad_inc = client.post(
                        "/api/v1/safety/incidents",
                        headers=headers,
                        json={"subject_id": "CREW-01", "incident_type": "WITNESS_REPORTED_UNCONSCIOUS"},
                    )
                    self.assertEqual(bad_inc.status_code, 422)

                    # Q-0055: UNANSWERED_CHECKIN never assumes unconsciousness
                    inc_resp = client.post(
                        "/api/v1/safety/incidents",
                        headers=headers,
                        json={
                            "subject_id": "CREW-01",
                            "incident_type": "UNANSWERED_CHECKIN",
                            "note": "No response after 2m",
                        },
                    )
                    self.assertEqual(inc_resp.status_code, 201, inc_resp.text)
                    inc = inc_resp.json()
                    self.assertFalse(inc["unconsciousness_assumed"])
                    self.assertTrue(inc["requires_human_or_witness_verification"])
                    inc_id = inc["incident_id"]

                    # Q-0059 before ACK: 1 total, 0 acked, inc_id pending
                    sync1 = client.get("/api/v1/sync/status", headers=headers, params={"subject_id": "CREW-01"})
                    self.assertEqual(sync1.status_code, 200)
                    s1 = sync1.json()
                    self.assertEqual(s1["server_version"], "0.2.0")
                    self.assertEqual(s1["incidents_total"], 1)
                    self.assertEqual(s1["incidents_acknowledged"], 0)
                    self.assertEqual(s1["pending_ack_incident_ids"], [inc_id])

                    # Q-0056: idempotent ACK retains same incident_id
                    ack1 = client.post(
                        f"/api/v1/safety/incidents/{inc_id}/ack",
                        headers=headers,
                        json={"note": "CMO checking crew"},
                    )
                    self.assertEqual(ack1.status_code, 200)
                    self.assertEqual(ack1.json()["incident_id"], inc_id)
                    self.assertEqual(ack1.json()["status"], "ACKNOWLEDGED")
                    self.assertFalse(ack1.json()["idempotent_replay"])

                    ack2 = client.post(
                        f"/api/v1/safety/incidents/{inc_id}/ack",
                        headers=headers,
                        json={"note": "Duplicate ACK"},
                    )
                    self.assertEqual(ack2.status_code, 200)
                    self.assertEqual(ack2.json()["incident_id"], inc_id)
                    self.assertTrue(ack2.json()["idempotent_replay"])

                    # Q-0056 negative: unknown incident_id -> 404
                    missing_ack = client.post(
                        "/api/v1/safety/incidents/inc-does-not-exist/ack",
                        headers=headers,
                        json={"note": "x"},
                    )
                    self.assertEqual(missing_ack.status_code, 404)

                    # Q-0059 after ACK: 1 total, 1 acked, 0 pending
                    sync2 = client.get("/api/v1/sync/status", headers=headers, params={"subject_id": "CREW-01"})
                    self.assertEqual(sync2.status_code, 200)
                    self.assertEqual(sync2.json()["incidents_acknowledged"], 1)
                    self.assertEqual(sync2.json()["pending_ack_incident_ids"], [])

                    # Q-0057: unknown device -> NO_DATA, connected=False (no fake sensor)
                    dev_unknown = client.get("/api/v1/devices/watch-unknown/status", headers=headers)
                    self.assertEqual(dev_unknown.status_code, 200)
                    self.assertEqual(dev_unknown.json()["signal_state"], "NO_DATA")
                    self.assertFalse(dev_unknown.json()["connected"])

                    # Q-0057: record offline heartbeat & verify SENSOR_OFFLINE + last_seen_at_utc
                    ts = datetime.now(timezone.utc).isoformat()
                    hb = client.post(
                        "/api/v1/devices/heartbeat",
                        headers=headers,
                        json={
                            "source_id": "watch-crew-01",
                            "subject_id": "CREW-01",
                            "link_connected": False,
                            "sensor_error": False,
                            "last_observed_at": ts,
                        },
                    )
                    self.assertEqual(hb.status_code, 200)
                    dev_st = client.get("/api/v1/devices/watch-crew-01/status", headers=headers)
                    self.assertEqual(dev_st.status_code, 200)
                    self.assertEqual(dev_st.json()["signal_state"], "SENSOR_OFFLINE")
                    self.assertFalse(dev_st.json()["connected"])
                    self.assertIsNotNone(dev_st.json()["last_seen_at_utc"])
                    self.assertFalse(dev_st.json()["medical_emergency"])
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
