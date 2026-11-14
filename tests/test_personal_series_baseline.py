"""Q-0081: source-backed trend requires two distinct timestamps; deny fakes."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

module = Path(__file__).resolve().parents[1] / 'apps/desktop/src/aetherion_desktop/features/personal/time_series_baseline.py'
spec = importlib.util.spec_from_file_location('personal_series_verified', module)
series = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = series
spec.loader.exec_module(series)
NOW = datetime(2026, 11, 14, 9, 20, tzinfo=timezone.utc)

def row(t='2026-11-14T09:10:00Z', v=70, **extra):
    d = dict(subject_id='CREW-1', scope='CREW', metric='heart_rate',
             value=v, unit='beats/min', source_id='human_entry', quality='READY',
             verification_state='SELF_REPORTED', observed_at=t, received_at=t)
    d.update(extra)
    return d

def response(*items, **extra):
    result = dict(subject_id='CREW-1', metric='heart_rate', points=list(items), count=len(items))
    result.update(extra)
    return result

class VerifiedPersonalSeriesTest(unittest.TestCase):
    def parse(self, payload=None, status=200):
        return series.personal_series_from_api('CREW-1', 'heart_rate', status,
                                               response() if payload is None else payload, now=NOW)

    def test_only_distinct_real_times_make_trend(self):
        result = self.parse(response(row(),row('2026-11-14T09:15:00Z',80)))
        self.assertTrue(result.can_plot)
        self.assertEqual(result.sample_reference_mean,75)
        self.assertEqual(result.status,'UNVERIFIED')
        self.assertEqual(result.points[0].source_id,'human_entry')

    def test_one_point_cannot_claim_reference_baseline(self):
        x=self.parse(response(row()))
        self.assertFalse(x.can_plot)
        self.assertIsNone(x.sample_reference_mean)

    def test_duplicate_timestamp_is_not_two_real_times(self):
        x=self.parse(response(row(),row(v=100)))
        self.assertFalse(x.can_plot)

    def test_no_data_and_network_fails_closed(self):
        self.assertEqual(self.parse().status,'NO_DATA')
        self.assertEqual(self.parse(status=403).status,'DENIED')
        self.assertEqual(self.parse(status=None).status,'OFFLINE')

    def test_other_subject_rejected(self):
        self.assertEqual(self.parse(response(row(subject_id='CREW-2'))).status,'ERROR')
        self.assertEqual(self.parse(response(subject_id='CREW-2')).status,'ERROR')

    def test_cabin_cannot_be_personal_trend(self):
        self.assertEqual(self.parse(response(row(scope='CABIN'))).status,'ERROR')

    def test_mixed_units_refused(self):
        self.assertEqual(self.parse(response(row(),row('2026-11-14T09:15:00Z',80,unit='bpm'))).status,'ERROR')

    def test_invalid_numbers_and_sources_fail_closed(self):
        for update in (dict(value=float('nan')),dict(value=True),dict(source_id=''),dict(quality='HEALTHY')):
            with self.subTest(update=update):
                self.assertEqual(self.parse(response(row(**update))).status,'ERROR')

    def test_naive_future_and_reception_clock_rejected(self):
        for update in (dict(observed_at='2026-11-14T09:10:00'),
                       dict(observed_at='2026-11-14T09:30:00Z',received_at='2026-11-14T09:30:00Z'),
                       dict(received_at='2026-11-14T09:09:00Z')):
            with self.subTest(update=update):
                self.assertEqual(self.parse(response(row(**update))).status,'ERROR')

    def test_research_and_fixture_not_live(self):
        for update in (dict(verification_state='TEST_FIXTURE'),dict(source_id='research:paper'),dict(source_id='nasa_osdr:study')):
            with self.subTest(update=update):
                self.assertEqual(self.parse(response(row(**update))).status,'NO_DATA')

    def test_verified_two_point_sample(self):
        a=row(verification_state='VERIFIED')
        b=row('2026-11-14T09:15:00Z',80,verification_state='VERIFIED')
        self.assertEqual(self.parse(response(a,b)).status,'READY')

    def test_timezone_aware_reference_clock_required(self):
        with self.assertRaises(ValueError):
            series.personal_series_from_api('CREW-1','heart_rate',200,response(),now=datetime(2026,11,14))

if __name__ == '__main__':
    unittest.main()
