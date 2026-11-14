"""Deterministic tests for Q-0168 (missing response vs unconsciousness) and Q-0169 (sensor technical alerts)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.server.src.aetherion_server.safety import (  # noqa: E402
    assess_checkin_response,
    evaluate_sensor_disconnection,
)


class SafetyResponseAndSensorAlertTests(unittest.TestCase):
    def test_unanswered_checkin_never_assumes_unconsciousness(self) -> None:
        now = datetime(2026, 11, 14, 9, 20, tzinfo=timezone.utc)
        res = assess_checkin_response(
            subject_id="crew-01",
            checkin_id="chk-101",
            response_received=False,
            now=now,
        )
        self.assertEqual(res.response_status, "UNANSWERED_CHECKIN")
        self.assertFalse(res.unconsciousness_assumed)
        self.assertFalse(res.medical_emergency_auto_declared)
        self.assertTrue(res.requires_human_or_witness_verification)
        self.assertIn("not prove unconsciousness", res.reason.lower())

    def test_witness_observed_unconscious_requires_witness_id(self) -> None:
        with self.assertRaises(ValueError):
            assess_checkin_response(
                subject_id="crew-01",
                checkin_id="chk-102",
                response_received=False,
                witness_observed_unconscious=True,
                witness_id=None,
            )

        res = assess_checkin_response(
            subject_id="crew-01",
            checkin_id="chk-102",
            response_received=False,
            witness_observed_unconscious=True,
            witness_id="crew-02",
        )
        self.assertEqual(res.response_status, "WITNESS_REPORTED_UNCONSCIOUS")
        self.assertFalse(res.unconsciousness_assumed)
        self.assertEqual(res.source, "witness:crew-02")

    def test_disconnected_and_stale_sensors_emit_technical_alert_not_medical_emergency(self) -> None:
        now = datetime(2026, 11, 14, 9, 20, tzinfo=timezone.utc)
        offline = evaluate_sensor_disconnection(
            alert_id="alt-1",
            source_id="watch-01",
            subject_id="crew-01",
            link_connected=False,
            sensor_error=False,
            last_observed_at=None,
            now=now,
        )
        self.assertIsNotNone(offline)
        assert offline is not None
        self.assertEqual(offline.alert_category, "TECHNICAL_ALERT")
        self.assertEqual(offline.technical_state, "SENSOR_OFFLINE")
        self.assertFalse(offline.medical_emergency)
        self.assertFalse(offline.inferred_unresponsiveness)
        self.assertTrue(offline.requires_device_check)

        stale_ts = (now - timedelta(seconds=600)).isoformat()
        stale = evaluate_sensor_disconnection(
            alert_id="alt-2",
            source_id="watch-01",
            subject_id="crew-01",
            link_connected=True,
            sensor_error=False,
            last_observed_at=stale_ts,
            stale_after_seconds=300.0,
            now=now,
        )
        self.assertIsNotNone(stale)
        assert stale is not None
        self.assertEqual(stale.technical_state, "STALE_SIGNAL")
        self.assertFalse(stale.medical_emergency)

    def test_fresh_connected_signal_emits_no_technical_alert(self) -> None:
        now = datetime(2026, 11, 14, 9, 20, tzinfo=timezone.utc)
        fresh_ts = (now - timedelta(seconds=15)).isoformat()
        res = evaluate_sensor_disconnection(
            alert_id="alt-3",
            source_id="watch-01",
            subject_id="crew-01",
            link_connected=True,
            sensor_error=False,
            last_observed_at=fresh_ts,
            stale_after_seconds=300.0,
            now=now,
        )
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()
