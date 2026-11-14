"""Focused verification for Q-0178 (false-positive audit) and Q-0179 (safety logic isolation from LLM)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.safety.assistance import AssistanceRequestStore
from aetherion_server.safety.incidents import IncidentRegistry
from aetherion_server.safety.response_semantics import assess_checkin_response
from aetherion_server.safety.technical_alerts import evaluate_sensor_disconnection


class SafetyFalsePositiveAndLlmIsolationTests(unittest.TestCase):
    def test_false_positive_separation_missing_sensor_no_reply_stale_and_witness(self) -> None:
        now = datetime(2026, 11, 14, 10, 0, 0, tzinfo=timezone.utc)

        # 1. Missing / disconnected sensor -> TECHNICAL_ALERT, not medical emergency
        missing = evaluate_sensor_disconnection(
            alert_id="alt-1",
            source_id="ecg-patch-1",
            subject_id="CREW-01",
            link_connected=False,
            sensor_error=False,
            last_observed_at=(now - timedelta(seconds=10)).isoformat(),
            now=now,
        )
        self.assertIsNotNone(missing)
        self.assertEqual(missing.alert_category, "TECHNICAL_ALERT")
        self.assertFalse(missing.medical_emergency)
        self.assertFalse(missing.inferred_unresponsiveness)

        # 2. Delayed packet (STALE) -> TECHNICAL_ALERT (STALE), not medical emergency
        stale = evaluate_sensor_disconnection(
            alert_id="alt-2",
            source_id="ecg-patch-1",
            subject_id="CREW-01",
            link_connected=True,
            sensor_error=False,
            last_observed_at=(now - timedelta(seconds=450)).isoformat(),
            stale_after_seconds=300.0,
            now=now,
        )
        self.assertIsNotNone(stale)
        self.assertEqual(stale.technical_state, "STALE_SIGNAL")
        self.assertFalse(stale.medical_emergency)

        # 3. No reply to check-in -> UNANSWERED_CHECKIN, unconsciousness_assumed=False
        no_reply = assess_checkin_response(
            subject_id="CREW-01",
            checkin_id="chk-1",
            response_received=False,
            now=now,
        )
        self.assertEqual(no_reply.response_status, "UNANSWERED_CHECKIN")
        self.assertFalse(no_reply.unconsciousness_assumed)
        self.assertFalse(no_reply.medical_emergency_auto_declared)
        self.assertTrue(no_reply.requires_human_or_witness_verification)

        # 4. User/witness-reported incident -> distinct WITNESS_REPORTED_UNCONSCIOUS
        witness = assess_checkin_response(
            subject_id="CREW-01",
            checkin_id="chk-2",
            response_received=False,
            witness_observed_unconscious=True,
            witness_id="CREW-02",
            now=now,
        )
        self.assertEqual(witness.response_status, "WITNESS_REPORTED_UNCONSCIOUS")
        self.assertFalse(witness.unconsciousness_assumed)
        self.assertEqual(witness.source, "witness:CREW-02")

    def test_safety_routing_and_classification_identical_with_ai_disabled_or_enabled(self) -> None:
        old_provider = os.environ.get("AETHERION_INTERVIEW_AI_PROVIDER")
        try:
            results = []
            for mode in ("disabled", "ollama"):
                os.environ["AETHERION_INTERVIEW_AI_PROVIDER"] = mode
                with tempfile.TemporaryDirectory() as tmpdir:
                    store = AssistanceRequestStore(Path(tmpdir) / "assist.sqlite3")
                    req = store.request_help(
                        subject_id="CREW-01",
                        actor_id="CREW-01",
                        reason="Need medical check",
                        telemetry_state="NO_DATA",
                        ai_enabled=(mode != "disabled"),
                    )
                    reg = IncidentRegistry()
                    inc = reg.create_incident(
                        incident_id="inc-fixed-1",
                        subject_id="CREW-01",
                        mission_id="M-2026",
                        incident_type="NEED_HELP_NOW",
                        source="crew_button",
                    )
                    reg.acknowledge_incident(
                        incident_id="inc-fixed-1",
                        acknowledged_by="CREW-02",
                        event_id="ev-1",
                    )
                    results.append((req["response_status"], req["telemetry_state"], inc.status, inc.incident_type))
            self.assertEqual(results[0], results[1])
            self.assertEqual(results[0], ("LOGGED_LOCAL_PENDING_ACK", "NO_DATA", "ACKNOWLEDGED", "NEED_HELP_NOW"))
        finally:
            if old_provider is None:
                os.environ.pop("AETHERION_INTERVIEW_AI_PROVIDER", None)
            else:
                os.environ["AETHERION_INTERVIEW_AI_PROVIDER"] = old_provider


if __name__ == "__main__":
    unittest.main()
