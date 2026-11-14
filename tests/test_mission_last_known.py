"""Focused privacy, timestamp and offline-display checks for Q-0071."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import importlib.util
from pathlib import Path
import sys
import unittest

source = Path(__file__).resolve().parents[1] / "apps/desktop/src/aetherion_desktop/features/mission/offline_last_known.py"
spec = importlib.util.spec_from_file_location("aetherion_last_known_test", source)
last_known = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = last_known
spec.loader.exec_module(last_known)
NOW = datetime(2026, 11, 14, 9, 18, tzinfo=timezone.utc)

@dataclass(frozen=True)
class Row:
    subject_id: str = "CREW-7"
    metric: str = "heart_rate"
    value: float = 70.0
    unit: str = "beats/min"
    observed_at: str = "2026-11-14T09:16:00Z"
    source_id: str = "human_entry"
    quality: str = "UNVERIFIED"
    verification_state: str = "SELF_REPORTED"

@dataclass(frozen=True)
class Snapshot:
    subject_id: str = "CREW-7"
    status: str = "UNVERIFIED"
    measurements: tuple = (Row(),)

class OfflineLastKnownTest(unittest.TestCase):
    def setUp(self):
        self.cache = last_known.LastKnownCache(stale_after_seconds=3600)
        self.cache.begin_authorized_scope("CREW-7", session_epoch=1)

    def snapshot(self, value=None):
        self.cache.record_authenticated_snapshot(Snapshot() if value is None else value, session_epoch=1)

    def test_no_ever_verified_data_means_offline_no_readings(self):
        self.cache.transport_lost()
        v = self.cache.view(now=NOW)
        self.assertEqual((v.state, v.readings), ("OFFLINE", ()))

    def test_recorded_source_age_offline_not_inferred_healthy(self):
        self.snapshot()
        self.cache.transport_lost()
        v = self.cache.view(now=NOW)
        self.assertEqual(v.state, "OFFLINE")
        self.assertEqual(len(v.readings), 1)
        self.assertEqual(v.readings[0].age_seconds, 120)
        self.assertEqual(v.readings[0].source_id, "human_entry")
        self.assertIn("Not current health", v.note)

    def test_hour_old_measurement_explicitly_stale(self):
        self.snapshot(Snapshot(measurements=(Row(observed_at="2026-11-14T08:00:00Z"),)))
        self.cache.transport_lost()
        v = self.cache.view(now=NOW)
        self.assertEqual(v.state, "STALE")
        self.assertEqual(v.readings[0].quality, "STALE")

    def test_same_session_keeps_original_timestamp_and_source(self):
        self.snapshot()
        self.cache.begin_authorized_scope("CREW-7", session_epoch=1)
        self.cache.transport_lost()
        v = self.cache.view(now=NOW)
        self.assertEqual(v.readings[0].observed_at, "2026-11-14T09:16:00+00:00")

    def test_another_subject_flushes_private_cache(self):
        self.snapshot()
        self.cache.begin_authorized_scope("CREW-8", session_epoch=1)
        self.cache.transport_lost()
        v = self.cache.view(now=NOW)
        self.assertEqual((v.subject_id, v.readings), ("CREW-8", ()))

    def test_different_login_epoch_flushes_private_cache(self):
        self.snapshot()
        self.cache.begin_authorized_scope("CREW-7", session_epoch=2)
        self.cache.transport_lost()
        self.assertEqual(self.cache.view(now=NOW).readings, ())

    def test_auth_denial_revokes_old_records(self):
        self.snapshot()
        self.cache.auth_error(403)
        v = self.cache.view(now=NOW)
        self.assertEqual((v.state, v.subject_id, v.readings), ("DENIED", None, ()))

    def test_cross_subject_reply_clears_auth_scope(self):
        self.snapshot()
        with self.assertRaises(ValueError):
            self.cache.record_authenticated_snapshot(Snapshot(subject_id="CREW-8"), session_epoch=1)
        self.assertEqual(self.cache.view(now=NOW).state, "DENIED")

    def test_incomplete_source_fails_without_adding_records(self):
        with self.assertRaises(ValueError):
            self.snapshot(Snapshot(measurements=(Row(source_id=""),)))
        self.cache.transport_lost()
        self.assertEqual(self.cache.view(now=NOW).readings, ())

    def test_time_in_future_hides_source(self):
        self.snapshot(Snapshot(measurements=(Row(observed_at="2026-11-14T10:00:00Z"),)))
        self.cache.transport_lost()
        v = self.cache.view(now=NOW)
        self.assertEqual((v.state, v.readings), ("ERROR", ())

    def test_no_data_snapshot_replaces_old_history(self):
        self.snapshot()
        self.snapshot(Snapshot(status="NO_DATA", measurements=()))
        self.cache.transport_lost()
        self.assertEqual(self.cache.view(now=NOW).readings, ())

    def test_login_requires_positive_epoch(self):
        with self.assertRaises(ValueError):
            self.cache.begin_authorized_scope("CREW-7", session_epoch=0)
        with self.assertRaises(ValueError):
            self.cache.begin_authorized_scope("CREW-7", session_epoch=True)

if __name__ == "__main__":
    unittest.main()
