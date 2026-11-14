"""Q-0083: care handoff never invents an episode link or user consent.

All records are synthetic contract fixtures; no patient/clinical data.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/desktop/src"))
from aetherion_desktop.features.personal.care_handoff import (
    prepare_consented_new_episode, resume_explicit_episode,
    selected_observation_from_api,
)


@dataclass(frozen=True)
class PersonalCard:
    metric: str = "heart_rate"
    reading: str = "72 beats/min"
    unit: str = "beats/min"
    source_id: str = "manual_unverified"
    scope: str = "CREW"
    quality: str = "UNVERIFIED"
    verification_state: str = "SELF_REPORTED"
    observed_at: str = "2026-11-14T09:00:00+00:00"


def record(**changes):
    row = dict(id=123, subject_id="CREW-7", metric="heart_rate", value=72,
               unit="beats/min", source_id="manual_unverified", scope="CREW",
               quality="UNVERIFIED", verification_state="SELF_REPORTED",
               observed_at="2026-11-14T09:00:00Z")
    row.update(changes)
    return row


def observations(*items, subject="CREW-7"):
    return {"subject_id": subject, "observations": list(items)}


class PersonalToCareTest(unittest.TestCase):
    def selection(self, *items, code=200, subject="CREW-7"):
        return selected_observation_from_api(
            subject, PersonalCard(), code,
            observations(*(items or (record(),)), subject=subject),
        )

    def test_exact_selected_measurement_found(self):
        selected = self.selection()
        self.assertEqual(selected.observation_id, 123)
        self.assertEqual(selected.source_id, "manual_unverified")
        self.assertEqual(selected.observed_at_utc, "2026-11-14T09:00:00+00:00")

    def test_no_authorized_server_read_no_selection(self):
        self.assertIsNone(self.selection(code=403))
        self.assertIsNone(self.selection(code=None))

    def test_mixed_identity_and_duplicate_measurements_fail_closed(self):
        self.assertIsNone(self.selection(record(), record(id=124, subject_id="CREW-8")))
        self.assertIsNone(self.selection(record(), record(id=124)))

    def test_wrong_value_or_time_cannot_be_matching_record(self):
        self.assertIsNone(self.selection(record(value=80)))
        self.assertIsNone(self.selection(record(observed_at="2026-11-14T09:01:00Z")))

    def test_research_and_engineering_fixture_not_crew_measurement(self):
        self.assertIsNone(self.selection(record(source_id="research:article")))
        self.assertIsNone(self.selection(record(verification_state="TEST_FIXTURE")))

    def test_existing_episode_requires_explicit_id(self):
        selected = self.selection()
        list_payload = {
            "subject_id": "CREW-7",
            "episodes": [{"episode_id": "ep-a", "subject_id": "CREW-7", "current_phase": "GATHER"}],
        }
        state = resume_explicit_episode(selected, 200, list_payload, None)
        self.assertEqual((state.status, state.episode_id), ("SELECT_EPISODE", None))
        chosen = resume_explicit_episode(selected, 200, list_payload, "ep-a")
        self.assertEqual(chosen.episode_id, "ep-a")
        self.assertFalse(chosen.observation_link_persisted)

    def test_unrelated_episode_never_chosen(self):
        selected = self.selection()
        list_payload = {
            "subject_id": "CREW-7",
            "episodes": [{"episode_id": "ep-a", "subject_id": "CREW-8", "current_phase": "GATHER"}],
        }
        result = resume_explicit_episode(selected, 200, list_payload, "ep-a")
        self.assertEqual(result.status, "ERROR")
        self.assertIsNone(result.episode_id)

    def test_closed_episode_not_resumed(self):
        selected = self.selection()
        payload = {"subject_id": "CREW-7", "episodes": [
            {"episode_id": "ep-closed", "subject_id": "CREW-7", "current_phase": "CLOSED"}]}
        self.assertEqual(resume_explicit_episode(selected, 200, payload, "ep-closed").status,
                         "CLOSED")

    def test_start_requires_human_consent_and_chief_concern(self):
        selected = self.selection()
        self.assertEqual(prepare_consented_new_episode(
            selected, "Concern entered by crew", explicit_consent=False).status,
            "CONSENT_REQUIRED")
        self.assertEqual(prepare_consented_new_episode(
            selected, " ", explicit_consent=True).status, "CONCERN_REQUIRED")

    def test_explicit_start_has_canonical_body_and_no_persisted_link_claim(self):
        state = prepare_consented_new_episode(
            self.selection(), "Crew-entered concern", explicit_consent=True)
        self.assertEqual(state.status, "CREATE_READY_UNLINKED")
        self.assertEqual(state.create_body["subject_id"], "CREW-7")
        self.assertTrue(state.create_body["explicit_consent"])
        self.assertEqual(state.create_body["chief_concern"], "Crew-entered concern")
        self.assertFalse(state.observation_link_persisted)
        self.assertNotIn("observation_id", state.create_body)


if __name__ == "__main__":
    unittest.main()
