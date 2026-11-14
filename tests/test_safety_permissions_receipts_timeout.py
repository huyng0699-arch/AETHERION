"""Focused API tests for Q-0173 (role-based incident details + audit), Q-0175 (receipts), and Q-0176 (timeout)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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

from aetherion_server.bootstrap import ensure_bootstrap_user
from aetherion_server.main import create_app


class SafetyPermissionsReceiptsTimeoutTests(unittest.TestCase):
    def test_permissions_audit_receipts_and_timeout_escalation(self) -> None:
        old_env = {
            k: os.environ.get(k)
            for k in ("AETHERION_BOOTSTRAP_USER", "AETHERION_BOOTSTRAP_PASSWORD", "AETHERION_BOOTSTRAP_ROLE")
        }
        os.environ["AETHERION_BOOTSTRAP_USER"] = "surgeon_lead"
        os.environ["AETHERION_BOOTSTRAP_PASSWORD"] = "surgeon-pass-123"
        os.environ["AETHERION_BOOTSTRAP_ROLE"] = "flight_surgeon"
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                db = Path(tmpdir) / "safety_perm.sqlite3"
                app = create_app(db_path=db)
                with TestClient(app) as client:
                    surgeon_token = client.post(
                        "/api/v1/auth/login",
                        json={"username": "surgeon_lead", "password": "surgeon-pass-123"},
                    ).json()["access_token"]
                    surgeon_hdr = {"Authorization": f"Bearer {surgeon_token}"}

                    ensure_bootstrap_user(
                        db,
                        username="ops_watch",
                        password="operator-pass-123",
                        role="operator",
                        allowed_subjects=["CREW-01"],
                    )
                    ops_token = client.post(
                        "/api/v1/auth/login",
                        json={"username": "ops_watch", "password": "operator-pass-123"},
                    ).json()["access_token"]
                    ops_hdr = {"Authorization": f"Bearer {ops_token}"}

                    # Report incident
                    inc = client.post(
                        "/api/v1/safety/incidents",
                        headers=surgeon_hdr,
                        json={
                            "subject_id": "CREW-01",
                            "incident_type": "WITNESS_REPORTED_UNCONSCIOUS",
                            "witness_id": "CREW-02",
                            "note": "Private clinical note: transient syncope reported",
                        },
                    ).json()
                    inc_id = inc["incident_id"]
                    self.assertEqual(inc["receipt_state"], "PENDING")
                    self.assertEqual(inc["escalation_state"], "NONE")

                    # Q-0173: Operator sees redacted personal note & witness_id; flight_surgeon sees full details
                    ops_detail = client.get(f"/api/v1/safety/incidents/{inc_id}", headers=ops_hdr)
                    self.assertEqual(ops_detail.status_code, 200)
                    self.assertTrue(ops_detail.json()["redacted"])
                    self.assertEqual(ops_detail.json()["note"], "[REDACTED_FOR_ROLE]")
                    self.assertIsNone(ops_detail.json()["witness_id"])

                    doc_detail = client.get(f"/api/v1/safety/incidents/{inc_id}", headers=surgeon_hdr)
                    self.assertEqual(doc_detail.status_code, 200)
                    self.assertFalse(doc_detail.json()["redacted"])
                    self.assertEqual(doc_detail.json()["witness_id"], "CREW-02")

                    # Q-0173: Audit log restricted to flight_surgeon/admin and records both accesses
                    self.assertEqual(client.get(f"/api/v1/safety/incidents/{inc_id}/audit", headers=ops_hdr).status_code, 403)
                    audit = client.get(f"/api/v1/safety/incidents/{inc_id}/audit", headers=surgeon_hdr).json()
                    self.assertEqual(len(audit["items"]), 2)
                    self.assertEqual(audit["items"][0]["actor_username"], "ops_watch")
                    self.assertTrue(audit["items"][0]["redacted"])
                    self.assertEqual(audit["items"][1]["actor_username"], "surgeon_lead")
                    self.assertFalse(audit["items"][1]["redacted"])

                    # Q-0175: Receipts start PENDING, transition to DELIVERED only with transport evidence
                    r_list0 = client.get(f"/api/v1/safety/incidents/{inc_id}/receipts", headers=surgeon_hdr).json()
                    self.assertEqual(r_list0["items"][0]["state"], "PENDING")
                    self.assertIsNone(r_list0["items"][0]["transport_evidence_id"])

                    bad_rcpt = client.post(
                        f"/api/v1/safety/incidents/{inc_id}/receipts",
                        headers=surgeon_hdr,
                        json={"channel": "onboard_bus", "transport_evidence_id": "   "},
                    )
                    self.assertEqual(bad_rcpt.status_code, 422)

                    deliv = client.post(
                        f"/api/v1/safety/incidents/{inc_id}/receipts",
                        headers=surgeon_hdr,
                        json={"channel": "onboard_bus", "transport_evidence_id": "tx-bus-991"},
                    )
                    self.assertEqual(deliv.status_code, 200)
                    self.assertEqual(deliv.json()["state"], "DELIVERED")

                    # Q-0176: Timeout triggers ESCALATED_PENDING_RESPONDER, never responder_confirmed
                    future = (datetime.now(timezone.utc) + timedelta(seconds=600)).isoformat()
                    esc = client.post(
                        f"/api/v1/safety/incidents/{inc_id}/evaluate-timeout",
                        headers=surgeon_hdr,
                        json={"timeout_seconds": 300, "now_utc": future},
                    )
                    self.assertEqual(esc.status_code, 200)
                    self.assertTrue(esc.json()["timed_out"])
                    self.assertEqual(esc.json()["escalation_state"], "ESCALATED_PENDING_RESPONDER")
                    self.assertFalse(esc.json()["responder_confirmed"])

                    # ACK transitions receipt to ACKNOWLEDGED
                    ack = client.post(
                        f"/api/v1/safety/incidents/{inc_id}/ack",
                        headers=surgeon_hdr,
                        json={"note": "Surgeon responding"},
                    )
                    self.assertEqual(ack.status_code, 200)
                    r_list1 = client.get(f"/api/v1/safety/incidents/{inc_id}/receipts", headers=surgeon_hdr).json()
                    self.assertEqual(r_list1["items"][0]["state"], "ACKNOWLEDGED")
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
