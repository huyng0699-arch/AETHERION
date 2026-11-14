"""Q-0093 isolated safety tests. All observations are synthetic engineering data."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

PATH = Path(__file__).resolve().parents[1] / "apps/server/src/aetherion_server/care/observation_gather.py"
spec = importlib.util.spec_from_file_location("aetherion_care_gather_test", PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
NOW = datetime(2026, 11, 14, 9, 0, tzinfo=timezone.utc)


def observation(**updates):
    data = dict(
        observation_uid="obs-test-1", subject_id="CREW-TEST-1",
        scope="CREW", metric="heart_rate", value=72.0,
        unit="beats/min", source_id="self_reported_test",
        quality="READY", verification_state="SELF_REPORTED",
        observed_at="2026-11-14T08:55:00Z",
        received_at="2026-11-14T08:55:02Z",
    )
    data.update(updates)
    return data


class CareGatherTests(unittest.TestCase):
    def gather(self, rows, **options):
        return mod.select_for_care_gather("CREW-TEST-1", rows, now=NOW, **options)

    def test_no_data_is_not_health(self):
        result = self.gather([])
        self.assertEqual((result.status, result.observations), ("NO_DATA", ()))

    def test_unverified_measurement_preserves_provenance(self):
        result = self.gather([observation()])
        self.assertEqual(result.status, "UNVERIFIED")
        first = result.observations[0]
        self.assertEqual(first.source_id, "self_reported_test")
        self.assertEqual(first.recorded_quality, "READY")
        self.assertEqual(first.effective_quality, "UNVERIFIED")

    def test_stale_value_never_appears_ready(self):
        row = observation(verification_state="VERIFIED",
                          observed_at="2026-11-10T08:00:00Z")
        result = self.gather([row])
        self.assertEqual(result.status, "STALE")

    def test_cross_subject_input_fails_closed_before_values(self):
        result = self.gather([observation(), observation(subject_id="CREW-OTHER", value=55)])
        self.assertEqual((result.status, result.observations), ("DENIED", ()))

    def test_nonlive_fixture_is_excluded_not_presented_as_crew_data(self):
        result = self.gather([observation(verification_state="TEST_FIXTURE")])
        self.assertEqual(result.status, "NO_DATA")
        self.assertEqual(result.ignored_non_live, 1)

    def test_missing_source_or_invalid_number_is_error(self):
        for changes in (
            {"source_id": ""},
            {"value": float("nan")},
            {"observed_at": "2026-11-14T09:00:00"},
            {"received_at": None},
        ):
            with self.subTest(changes=changes):
                result = self.gather([observation(**changes)])
                self.assertEqual(result.status, "ERROR")
                self.assertEqual(result.observations, ())

    def test_exact_selection_does_not_invent_other_records(self):
        rows = [observation(), observation(observation_uid="obs-test-2", metric="spo2", unit="%")]
        only = self.gather(rows, selected_observation_uids={"obs-test-2"})
        self.assertEqual(len(only.observations), 1)
        self.assertEqual(only.observations[0].metric, "spo2")
        none = self.gather(rows, selected_observation_uids={"missing"})
        self.assertEqual((none.status, none.observations), ("NO_DATA", ()))

    def test_future_verified_time_is_not_ready(self):
        result = self.gather([observation(verification_state="VERIFIED",
                                         observed_at="2026-11-17T09:00:00Z")])
        self.assertEqual(result.status, "UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
