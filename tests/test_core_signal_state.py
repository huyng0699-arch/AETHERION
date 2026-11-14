"""Tests for Q-0036 technical source state vs clinical incident separation."""

from datetime import datetime, timedelta, timezone
import unittest

from aetherion_server.signal_state import classify_technical_source_state


class SignalStateTests(unittest.TestCase):
    def test_missing_offline_and_stale_signals_never_infer_unresponsiveness(self) -> None:
        now = datetime(2026, 11, 14, 5, 15, 0, tzinfo=timezone.utc)

        no_sig = classify_technical_source_state(
            source_id="wearable_1",
            subject_id="CREW-1",
            link_connected=True,
            sensor_error=False,
            last_observed_at=None,
            now=now,
        )
        self.assertEqual(no_sig.technical_state, "NO_SIGNAL")
        self.assertFalse(no_sig.inferred_unresponsiveness)
        self.assertFalse(no_sig.clinical_incident_inferred)

        offline = classify_technical_source_state(
            source_id="wearable_1",
            subject_id="CREW-1",
            link_connected=False,
            sensor_error=False,
            last_observed_at=now.isoformat(),
            now=now,
        )
        self.assertEqual(offline.technical_state, "SENSOR_OFFLINE")
        self.assertFalse(offline.inferred_unresponsiveness)
        self.assertFalse(offline.clinical_incident_inferred)

        stale = classify_technical_source_state(
            source_id="wearable_1",
            subject_id="CREW-1",
            link_connected=True,
            sensor_error=False,
            last_observed_at=(now - timedelta(minutes=10)).isoformat(),
            stale_after_seconds=300.0,
            now=now,
        )
        self.assertEqual(stale.technical_state, "STALE_SIGNAL")
        self.assertFalse(stale.inferred_unresponsiveness)
        self.assertFalse(stale.clinical_incident_inferred)

    def test_naive_timestamp_or_empty_source_rejected(self) -> None:
        with self.assertRaises(ValueError):
            classify_technical_source_state(
                source_id="",
                subject_id="CREW-1",
                link_connected=True,
                sensor_error=False,
                last_observed_at=None,
            )
        with self.assertRaises(ValueError):
            classify_technical_source_state(
                source_id="wearable_1",
                subject_id="CREW-1",
                link_connected=True,
                sensor_error=False,
                last_observed_at="2026-11-14T05:15:00",
            )


if __name__ == "__main__":
    unittest.main()
