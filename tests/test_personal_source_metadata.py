"""Q-0086: source detail authenticity, device uncertainty and privacy checks."""
from dataclasses import dataclass
import importlib.util
from pathlib import Path
import sys
import unittest

p = Path(__file__).resolve().parents[1] / 'apps/desktop/src/aetherion_desktop/features/personal/source_metadata_inspector.py'
spec = importlib.util.spec_from_file_location('source_metadata_fixture', p)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

@dataclass(frozen=True)
class Card:
    metric:str='heart_rate'
    reading:str='70 beats/min'
    source_id:str='human_entry'
    scope:str='CREW'
    observed_at:str='2026-11-14T09:30:00Z'
    quality:str='UNVERIFIED'
    verification_state:str='SELF_REPORTED'

def original(**changes):
    d=dict(subject_id='CREW-1',metric='heart_rate',source_id='human_entry',scope='CREW',
           observed_at='2026-11-14T09:30:00Z',received_at='2026-11-14T09:31:00Z',device_id='device-claimed')
    d.update(changes);return d

class Inspector(unittest.TestCase):
    def inspect(self,card=None,source=None):
        return mod.source_detail_from_card(card or Card(),selected_subject_id='CREW-1',original=source)
    def test_unknown_device_is_explicit(self):
        v=self.inspect();self.assertEqual(v.device_identity,'NOT PROVIDED');self.assertIn('no verified',v.device_evidence.lower())
    def test_reported_device_not_certified(self):
        v=self.inspect(source=original());self.assertEqual(v.device_identity,'device-claimed');self.assertIn('not independently',v.device_evidence)
    def test_original_measurement_source_timestamp(self):
        v=self.inspect(source=original());self.assertEqual(v.source_id,'human_entry');self.assertIn('+00:00',v.observed_at_utc)
    def test_other_subject_denied(self):
        with self.assertRaises(ValueError):self.inspect(source=original(subject_id='CREW-2'))
    def test_wrong_metric_source_or_scope_denied(self):
        for change in (dict(metric='ECG'),dict(scope='CABIN'),dict(source_id='unknown')):
            with self.subTest(change=change),self.assertRaises(ValueError):self.inspect(source=original(**change))
    def test_naive_time_denied(self):
        with self.assertRaises(ValueError):self.inspect(source=original(observed_at='2026-11-14T09:30:00'))
    def test_wrong_time_denied(self):
        with self.assertRaises(ValueError):self.inspect(source=original(observed_at='2026-11-14T09:29:00Z'))
    def test_received_before_measured_denied(self):
        with self.assertRaises(ValueError):self.inspect(source=original(received_at='2026-11-14T09:29:00Z'))
    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError):self.inspect(card=Card(source_id=''))
    def test_unknown_quality_rejected(self):
        with self.assertRaises(ValueError):self.inspect(card=Card(quality='NORMAL'))
    def test_verified_does_not_mean_device(self):
        v=self.inspect(card=Card(quality='READY',verification_state='VERIFIED'))
        self.assertIn('no clinical',v.note)

if __name__=='__main__':unittest.main()
