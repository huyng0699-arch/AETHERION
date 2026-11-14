"""Q-0065: synthetic engineering fixtures only; no real patient incidents."""
from pathlib import Path
import importlib.util
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'apps/desktop/src/aetherion_desktop/features/mission/event_list.py'
spec = importlib.util.spec_from_file_location('event_list_fixture', MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

TIME = '2026-11-14T04:00:00Z'


def technical(**extra):
    data = dict(event_id='tech-1', title='Device connection failure', kind='TECHNICAL',
                scope='DEVICE', source_id='gateway-log', observed_at=TIME)
    data.update(extra)
    return data


def report(**extra):
    data = dict(event_id='user-1', title='Reported headache', kind='SELF_REPORTED',
                scope='CREW', subject_id='crew-A', source_kind='SELF_REPORTED',
                source_id='authenticated-user', observed_at=TIME)
    data.update(extra)
    return data


class EventListTests(unittest.TestCase):
    def test_no_data_means_no_incidents(self):
        result = mod.split_events([], [])
        self.assertEqual((result.technical, result.health, result.withheld), ((), (), 0))

    def test_mixed_events_have_separate_surfaces(self):
        result = mod.split_events([report(), technical()], ['crew-A'])
        self.assertEqual(len(result.technical), 1)
        self.assertEqual(len(result.health), 1)
        self.assertEqual(result.health[0].kind, 'SELF_REPORTED')

    def test_private_subject_is_withheld(self):
        result = mod.split_events([report()], ['crew-B'])
        self.assertEqual(result.health, ())
        self.assertEqual(result.withheld, 1)

    def test_bad_provenance_and_unknown_type_are_rejected(self):
        for row in (technical(source_id=''), technical(kind='AUTO_DIAGNOSIS'),
                    report(source_kind='SENSOR'), technical(observed_at='2026-11-14T04:00:00')):
            with self.assertRaises(ValueError):
                mod.split_events([row], ['crew-A'])

    def test_clinical_label_requires_explicit_reviewer(self):
        candidate = report(kind='CLINICAL_REVIEWED', source_kind='CLINICAL_REVIEWED')
        with self.assertRaises(ValueError):
            mod.split_events([candidate], ['crew-A'])
        candidate.update(reviewer_id='clinician-1', reviewed_at=TIME)
        self.assertEqual(mod.split_events([candidate], ['crew-A']).health[0].kind, 'CLINICAL_REVIEWED')

    def test_no_crew_in_technical_incident(self):
        with self.assertRaises(ValueError):
            mod.split_events([technical(subject_id='crew-A')], ['crew-A'])

    def test_duplicate_event_ids_rejected(self):
        with self.assertRaises(ValueError):
            mod.split_events([technical(), technical()], [])

    def test_future_server_integration_can_sort_by_time(self):
        early = technical(event_id='t1', observed_at='2026-11-13T02:00:00Z')
        late = technical(event_id='t2', observed_at='2026-11-14T03:00:00Z')
        out = mod.split_events([early, late], [])
        self.assertEqual([r.event_id for r in out.technical], ['t2', 't1'])


if __name__ == '__main__':
    unittest.main()
