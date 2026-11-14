"""E2E test for Q-0248: Safety missing-signal / lost heartbeat never creates unconsciousness classification."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
for p in (str(REPO_ROOT), str(SERVER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from apps.server.src.aetherion_server.safety import (  # noqa: E402
    assess_checkin_response,
    evaluate_sensor_disconnection,
)
from apps.server.src.aetherion_server.safety.incidents import IncidentRegistry  # noqa: E402


class SafetyMissingSignalE2ETests(unittest.TestCase):
    def test_lost_heartbeat_and_unanswered_checkin_never_classify_unconscious(self) -> None:
        now = datetime(2026, 11, 14, 9, 32, tzinfo=timezone.utc)

        # 1. Lost heartbeat / OFFLINE wearable signal -> TECHNICAL_ALERT, not medical emergency
        alert = evaluate_sensor_disconnection(
            alert_id="alt-hb-lost-1",
            source_id="wearable-crew-01",
            subject_id="CREW-01",
            link_connected=False,
            sensor_error=False,
            last_observed_at=now.isoformat(),
            now=now,
        )
        self.assertIsNotNone(alert)
        assert alert is not None
        self.assertEqual(alert.alert_category, "TECHNICAL_ALERT")
        self.assertFalse(alert.medical_emergency)
        self.assertFalse(alert.inferred_unresponsiveness)
        self.assertEqual(alert.technical_state, "SENSOR_OFFLINE")

        # 2. Unanswered check-in after lost signal -> UNANSWERED_CHECKIN, unconsciousness_assumed=False
        checkin = assess_checkin_response(
            subject_id="CREW-01",
            checkin_id="chk-hb-lost-1",
            response_received=False,
            now=now,
        )
        self.assertEqual(checkin.response_status, "UNANSWERED_CHECKIN")
        self.assertFalse(checkin.unconsciousness_assumed)
        self.assertFalse(checkin.medical_emergency_auto_declared)
        self.assertTrue(checkin.requires_human_or_witness_verification)

        # 3. Routing an assistance/check-in request preserves subject identity without auto-declaring unconscious
        reg = IncidentRegistry()
        inc = reg.create_incident(
            incident_id="inc-hb-lost-1",
            subject_id="CREW-01",
            mission_id="lunar-hab-1",
            incident_type="UNANSWERED_CHECKIN",
            source="safety_monitor",
            now=now,
        )
        self.assertEqual(inc.subject_id, "CREW-01")
        self.assertNotIn("UNCONSCIOUS", inc.incident_type)


if __name__ == "__main__":
    unittest.main()
