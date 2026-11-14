"""Q-0062 headless state contract checks using synthetic engineering fixtures only."""
from __future__ import annotations

from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = (Path(__file__).resolve().parents[1]
          / "apps/desktop/src/aetherion_desktop/features/mission/crew_data_state.py")
spec = importlib.util.spec_from_file_location("aetherion_crew_data_state_for_tests", MODULE)
state = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = state
spec.loader.exec_module(state)
NOW = datetime(2026, 11, 14, 6, 0, tzinfo=timezone.utc)


def observation(**changes):
    item = dict(subject_id="CREW-7", metric="heart_rate", value=72.0, unit="beats/min",
                source_id="manual_unverified", scope="CREW",
                observed_at="2026-11-14T05:30:00Z", received_at="2026-11-14T05:31:00Z",
                quality="READY", verification_state="SELF_REPORTED")
    item.update(changes)
    return item


def page(*records, **changes):
    data = dict(subject_id="CREW-7", observations=list(records), has_more=False,
                next_cursor=None)
    data.update(changes)
    return data


class CrewDataStateTests(unittest.TestCase):
    def parse(self, status, payload=None, **kw):
        return state.state_from_server_response("CREW-7", status, payload, now=NOW, **kw)

    def test_empty_api_is_no_data_not_healthy(self):
        value = self.parse(200, page())
        self.assertEqual(value.status, "NO_DATA")
        self.assertFalse(value.measurements)

    def test_no_network_is_offline_not_unconscious(self):
        for status in (None, 503):
            value = self.parse(status)
            self.assertEqual(value.status, "OFFLINE")
            self.assertEqual(value.measurements, ())
        self.assertIn("no crew health status", self.parse(None).message.lower())

    def test_access_denial_cannot_expose_measurements(self):
        for status in (401, 403):
            value = self.parse(status, page(observation()))
            self.assertEqual(value.status, "DENIED")
            self.assertFalse(value.measurements)

    def test_http_error_fails_closed(self):
        self.assertEqual(self.parse(500, page(observation())).status, "ERROR")

    def test_source_backed_unverified_reading_preserved(self):
        result = self.parse(200, page(observation()))
        self.assertEqual(result.status, "UNVERIFIED")
        self.assertEqual(result.measurements[0].value, 72.0)
        self.assertEqual(result.measurements[0].source_id, "manual_unverified")
        self.assertEqual(result.measurements[0].verification_state, "SELF_REPORTED")

    def test_verified_old_reading_is_stale(self):
        result = self.parse(200, page(observation(quality="READY", verification_state="VERIFIED",
                          observed_at="2026-11-13T05:30:00Z", received_at="2026-11-13T05:32:00Z")))
        self.assertEqual(result.status, "STALE")
        self.assertEqual(result.measurements[0].quality, "STALE")

    def test_proper_verified_current_reading(self):
        result = self.parse(200, page(observation(verification_state="VERIFIED")))
        self.assertEqual(result.status, "READY")
        self.assertEqual(result.last_observed_at, "2026-11-14T05:30:00+00:00")

    def test_mismatched_subject_response_fails_closed(self):
        for payload in (page(subject_id="CREW-8"), page(observation(subject_id="CREW-8"))):
            result = self.parse(200, payload)
            self.assertEqual((result.status, result.measurements), ("ERROR", ()))

    def test_missing_or_bad_source_time_value_fails_closed(self):
        for changes in (dict(source_id=""), dict(received_at=None), dict(observed_at="2026-11-14T05:30:00"),
                        dict(value=float("nan")), dict(value=True), dict(received_at="2026-11-14T05:00:00Z"),
                        dict(quality="HEALTHY")):
            with self.subTest(changes=changes):
                self.assertEqual(self.parse(200, page(observation(**changes))).status, "ERROR")

    def test_test_fixtures_and_nasa_research_are_not_live(self):
        for changes in (dict(verification_state="TEST_FIXTURE"), dict(scope="engineering_test"),
                        dict(source_id="nasa_osdr:study"), dict(source_id="research:paper")):
            with self.subTest(changes=changes):
                r = self.parse(200, page(observation(**changes)))
                self.assertEqual((r.status, r.measurements), ("NO_DATA", ()))

    def test_invalid_pagination_rejected(self):
        for payload in (page(observation(), has_more=True), page(observation(), has_more="yes"),
                        page(observation(), next_cursor=4), page(has_more=True, next_cursor="token")):
            with self.subTest(payload=payload):
                self.assertEqual(self.parse(200, payload).status, "ERROR")

    def test_valid_continuation_propagated(self):
        result = self.parse(200, page(observation(), has_more=True, next_cursor="safe_token"))
        self.assertTrue(result.has_more)
        self.assertEqual(result.next_cursor, "safe_token")

    def test_future_observation_cannot_be_ready(self):
        item = observation(observed_at="2026-11-14T06:30:00Z", received_at="2026-11-14T06:31:00Z",
                           verification_state="VERIFIED")
        self.assertEqual(self.parse(200, page(item)).status, "UNVERIFIED")

    def test_bad_reference_clock_rejected(self):
        with self.assertRaises(ValueError):
            state.state_from_server_response("CREW-7", 200, page(), now=datetime(2026, 11, 14))

    def test_mixed_research_and_measurement_is_labeled(self):
        result = self.parse(200, page(observation(), observation(source_id="research:article")))
        self.assertEqual(len(result.measurements), 1)
        self.assertIn("excluded", result.message)


if __name__ == "__main__":
    unittest.main()
