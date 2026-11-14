"""Q-0061 deterministic model checks. All records are synthetic engineering fixtures."""
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import sys
import unittest

MODULE = Path(__file__).with_name('mission_control.py')
spec = importlib.util.spec_from_file_location('mission_control_fixture', MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

NOW = datetime(2026, 11, 14, 6, 0, tzinfo=timezone.utc)


def item(**extra):
    return dict(subject_id='CREW-1', metric='heart_rate', value=70, unit='beats/min',
                observed_at='2026-11-14T05:30:00+00:00', source_id='human_entry',
                scope='CREW', quality='READY', verification_state='SELF_REPORTED', **extra)


class MissionModelTests(unittest.TestCase):
    def test_url_encodes_subject_preventing_query_injection(self):
        url = mod.observation_url('http://127.0.0.1:8765/', 'ABC&limit=500')
        self.assertIn('subject_id=ABC%26limit%3D500', url)
        self.assertTrue(url.endswith('&limit=100'))

    def test_invalid_subject_rejected(self):
        for identifier in ('', 'a' * 81, 'bad\nvalue'):
            with self.assertRaises(ValueError):
                mod.observation_url('http://127.0.0.1:8765', identifier)

    def test_empty_is_no_data_not_healthy(self):
        snap = mod.parse_observations({'subject_id': 'CREW-1', 'observations': []}, 'CREW-1', now=NOW)
        self.assertEqual(snap.state, 'NO_DATA')
        self.assertEqual(snap.rows, ())

    def test_unverified_manual_record_never_labelled_verified(self):
        snap = mod.parse_observations({'subject_id': 'CREW-1', 'observations': [item()]}, 'CREW-1', now=NOW)
        self.assertEqual(snap.state, 'READY')
        self.assertEqual(snap.rows[0].quality, 'UNVERIFIED')
        self.assertEqual(snap.rows[0].source_id, 'human_entry')

    def test_identity_mismatch_fails_closed(self):
        for data in ({'subject_id': 'CREW-2', 'observations': []},
                     {'subject_id': 'CREW-1', 'observations': [dict(item(), subject_id='CREW-2')]}):
            snap = mod.parse_observations(data, 'CREW-1', now=NOW)
            self.assertEqual((snap.state, snap.rows), ('ERROR', ()))

    def test_absent_source_and_nonfinite_rejected(self):
        for row in (dict(item(), source_id=''), dict(item(), value=float('nan')),
                    dict(item(), observed_at='2026-11-14T05:00:00')):
            snap = mod.parse_observations({'subject_id': 'CREW-1', 'observations': [row]}, 'CREW-1', now=NOW)
            self.assertEqual(snap.state, 'ERROR')

    def test_stale_ready_measurement(self):
        row = dict(item(), verification_state='VERIFIED', observed_at='2026-11-12T05:00:00+00:00')
        snap = mod.parse_observations({'subject_id': 'CREW-1', 'observations': [row]}, 'CREW-1', now=NOW)
        self.assertEqual(snap.rows[0].quality, 'STALE')

    def test_future_time_not_claimed_ready(self):
        row = dict(item(), verification_state='VERIFIED', observed_at='2026-11-17T05:00:00+00:00')
        snap = mod.parse_observations({'subject_id': 'CREW-1', 'observations': [row]}, 'CREW-1', now=NOW)
        self.assertEqual(snap.rows[0].quality, 'UNVERIFIED')

    def test_true_server_pagination_indicator(self):
        snap = mod.parse_observations({'subject_id': 'CREW-1', 'observations': [item()], 'has_more': True},
                                     'CREW-1', now=NOW)
        self.assertTrue(snap.has_more)


if __name__ == '__main__':
    unittest.main()
