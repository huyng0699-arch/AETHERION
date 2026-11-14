"""Synthetic source-backed series regressions; no native Windows claim."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "apps/desktop/src/aetherion_desktop/features/mission/time_series.py"
spec = importlib.util.spec_from_file_location("mission_time_series", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
NOW = datetime(2026, 11, 14, 6, 0, tzinfo=timezone.utc)


def obs(t="2026-11-14T05:00:00Z", value=70, **update):
    o = dict(subject_id="CREW-5", metric="heart_rate", scope="CREW", value=value,
             unit="beats/min", source_id="human_entry", quality="UNVERIFIED",
             verification_state="SELF_REPORTED", observed_at=t, received_at=t)
    o.update(update)
    return o


def payload(*items, **updates):
    v = dict(subject_id="CREW-5", metric="heart_rate", points=list(items), count=len(items))
    v.update(updates)
    return v


class SeriesTests(unittest.TestCase):
    def parse(self, data, code=200):
        return mod.from_series_api("CREW-5", "heart_rate", code, data, now=NOW)

    def test_two_actual_points_allow_two_dimensional_plot(self):
        s = self.parse(payload(obs(), obs("2026-11-14T05:10:00Z", 76)))
        self.assertTrue(s.can_plot)
        self.assertEqual(len(s.points), 2)
        self.assertEqual(s.status, "UNVERIFIED")
        self.assertEqual(s.points[1].source_id, "human_entry")

    def test_no_point_does_not_claim_trend(self):
        s = self.parse(payload())
        self.assertEqual(s.status, "NO_DATA")
        self.assertFalse(s.can_plot)

    def test_one_point_does_not_claim_trend(self):
        s = self.parse(payload(obs()))
        self.assertFalse(s.can_plot)
        self.assertIn("trend unavailable", s.note)

    def test_two_records_same_time_no_trend(self):
        s = self.parse(payload(obs(value=70), obs(value=80)))
        self.assertFalse(s.can_plot)

    def test_bad_subject_metric_or_count_fails_closed(self):
        for data in (payload(subject_id="OTHER"), payload(metric="oxygen"),
                     payload(obs(subject_id="OTHER")), payload(obs(metric="oxygen")),
                     payload(obs(), count=3)):
            with self.subTest(data=data):
                self.assertEqual(self.parse(data).status, "ERROR")

    def test_denied_offline_error_hide_points(self):
        for code, expected in ((401,"DENIED"), (403,"DENIED"), (503,"OFFLINE"), (500,"ERROR"), (None,"OFFLINE")):
            with self.subTest(code=code):
                s = self.parse(payload(obs(), obs("2026-11-14T05:10:00Z")), code)
                self.assertEqual((s.status, s.points, s.can_plot), (expected, (), False))

    def test_bad_source_or_nonfinite_or_naive_time_fails_closed(self):
        for x in (dict(source_id=""), dict(value=float("nan")), dict(value=True),
                  dict(observed_at="2026-11-14T05:00:00"), dict(received_at=None)):
            with self.subTest(x=x):
                self.assertEqual(self.parse(payload(obs(**x))).status, "ERROR")

    def test_units_must_match(self):
        s = self.parse(payload(obs(), obs("2026-11-14T05:10:00Z", unit="bpm")))
        self.assertEqual((s.status, s.can_plot), ("ERROR", False))

    def test_research_and_test_fixture_never_live(self):
        for x in (dict(verification_state="TEST_FIXTURE"),dict(source_id="research:paper"),
                  dict(source_id="nasa_osdr:study"),dict(scope="engineering_test")):
            with self.subTest(x=x):
                s = self.parse(payload(obs(**x), obs("2026-11-14T05:10:00Z", **x)))
                self.assertEqual(s.status, "NO_DATA")

    def test_future_measurement_rejected(self):
        self.assertEqual(self.parse(payload(obs("2026-11-14T06:20:00Z"))).status, "ERROR")

    def test_order_is_timestamp_not_input_arrival(self):
        s = self.parse(payload(obs("2026-11-14T05:30:00Z", 80), obs("2026-11-14T05:10:00Z", 70)))
        self.assertEqual([p.value for p in s.points], [70, 80])

    def test_verified_but_unvalidated_source_is_not_forced_ready(self):
        s = self.parse(payload(obs(verification_state="VERIFIED", quality="READY"),
                               obs("2026-11-14T05:10:00Z", verification_state="VERIFIED",quality="READY")))
        self.assertEqual(s.status, "READY")
        self.assertTrue(s.can_plot)


if __name__ == "__main__":
    unittest.main()
