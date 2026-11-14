"""Tests for Need Help Now deterministic assistance request store (Q-0166)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SERVER_SRC = Path(__file__).resolve().parents[1] / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.safety.assistance import AssistanceRequestStore


class TestSafetyAssistance(unittest.TestCase):
    def test_help_request_works_without_ai_and_does_not_fabricate_ack(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AssistanceRequestStore(Path(tmpdir) / "safety.sqlite")
            req = store.request_help(
                subject_id="CREW-03",
                actor_id="CREW-03",
                location="Node 2",
                reason="Severe vertigo during transfer",
                telemetry_state="NO_DATA",
                ai_enabled=False,
                requested_at="2026-11-14T09:00:00+00:00",
            )
            self.assertFalse(req["ai_enabled"])
            self.assertEqual(req["source"], "USER_ACTION")
            self.assertEqual(req["telemetry_state"], "NO_DATA")
            self.assertEqual(req["response_status"], "LOGGED_LOCAL_PENDING_ACK")
            self.assertIsNone(req["responder_id"])

            acked = store.acknowledge_request(
                req["request_id"],
                responder_id="CMO-01",
                acknowledged_at="2026-11-14T09:01:00+00:00",
            )
            self.assertEqual(acked["response_status"], "ACKNOWLEDGED_BY_CREW")
            self.assertEqual(acked["responder_id"], "CMO-01")
            self.assertEqual(len(store.list_requests(subject_id="CREW-03")), 1)

    def test_negative_invalid_inputs_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = AssistanceRequestStore(Path(tmpdir) / "safety_neg.sqlite")
            with self.assertRaises(ValueError):
                store.request_help(subject_id="", actor_id="CREW-01", reason="Help")
            with self.assertRaises(ValueError):
                store.request_help(subject_id="CREW-01", actor_id="CREW-01", reason="Help", telemetry_state="FAKE")
            with self.assertRaises(ValueError):
                store.request_help(
                    subject_id="CREW-01",
                    actor_id="CREW-01",
                    reason="Help",
                    requested_at="2026-11-14T09:00:00",
                )


if __name__ == "__main__":
    unittest.main()
