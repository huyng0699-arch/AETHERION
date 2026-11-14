"""Q-0084 privacy regressions; synthetic notes, never actual patient content."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import unittest

SOURCE = (Path(__file__).resolve().parents[1] /
          "apps/desktop/src/aetherion_desktop/features/personal/narrative_privacy.py")
spec = importlib.util.spec_from_file_location("aetherion_private_notes_test", SOURCE)
privacy = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = privacy
spec.loader.exec_module(privacy)


def access(**overrides):
    values = dict(role="crew", verified_subject_id="CREW-A",
                  can_read_private_text=True, server_authorized=True)
    values.update(overrides)
    return privacy.NarrativeAccess(**values)


def note(**overrides):
    values = dict(subject_id="CREW-A", text="Private synthetic text for testing",
                  source_id="personal_self_report", observed_at="2026-11-14T09:00:00Z")
    values.update(overrides)
    return values


class NarrativePrivacyTests(unittest.TestCase):
    def project(self, grant=None, records=None, status=200, subject="CREW-A"):
        if records is None:
            records = [note()]
        return privacy.private_narrative_projection(
            subject, access() if grant is None else grant, records, http_status=status
        )

    def test_explicit_verified_self_grant_allows_source_identified_text(self):
        result = self.project()
        self.assertEqual((result.status, result.subject_id), ("READY", "CREW-A"))
        self.assertEqual(result.records[0].text, "Private synthetic text for testing")
        self.assertEqual(result.records[0].source_id, "personal_self_report")

    def test_unauthorized_roles_cannot_see_even_with_broad_metric_access(self):
        for role in ("operator", "admin", "flight_surgeon", "guest"):
            with self.subTest(role=role):
                result = self.project(grant=access(role=role))
                self.assertEqual((result.status, result.subject_id, result.records),
                                 ("DENIED", None, ()))

    def test_generic_observation_permission_is_not_private_note_consent(self):
        for grant in (access(can_read_private_text=False),
                      access(server_authorized=False)):
            with self.subTest(grant=grant):
                self.assertEqual(self.project(grant=grant).records, ())
                self.assertIsNone(self.project(grant=grant).subject_id)

    def test_cross_subject_or_unbound_view_is_denied(self):
        for grant in (access(verified_subject_id="CREW-B"),
                      access(verified_subject_id=None)):
            with self.subTest(grant=grant):
                self.assertEqual(self.project(grant=grant).status, "DENIED")

    def test_401_403_and_missing_session_no_private_data(self):
        for status in (401, 403, None):
            with self.subTest(status=status):
                result = self.project(status=status)
                self.assertEqual((result.subject_id, result.records), (None, ()))

    def test_cross_subject_note_fails_atomically(self):
        result = self.project(records=[note(), note(subject_id="CREW-B")])
        self.assertEqual((result.status, result.records), ("ERROR", ()))

    def test_missing_origin_naive_time_and_empty_note_fail_closed(self):
        for changes in (dict(source_id=""), dict(observed_at="2026-11-14T09:00:00"),
                        dict(text="")):
            with self.subTest(changes=changes):
                result = self.project(records=[note(**changes)])
                self.assertEqual((result.status, result.records), ("ERROR", ()))

    def test_no_data_is_not_a_private_message(self):
        result = self.project(records=[])
        self.assertEqual((result.status, result.records), ("NO_DATA", ()))

    def test_original_private_words_are_not_rewritten_for_ui_language(self):
        message = "Tôi buồn hôm nay — private diary, not an AI diagnosis"
        result = self.project(records=[note(text=message)])
        self.assertEqual(result.records[0].text, message)

    def test_crew_overview_whitelist_removes_notes_and_metadata(self):
        leaked = privacy.strip_private_fields_for_crew_overview({
            "subject_id": "CREW-A", "metric": "heart_rate", "value": 71,
            "note": "PRIVATE", "mood_text": "PRIVATE", "summary": "PRIVATE",
            "record_count": 12, "narrative_id": "SECRET",
        })
        self.assertEqual(leaked, {"subject_id": "CREW-A", "metric": "heart_rate", "value": 71})
        self.assertNotIn("PRIVATE", str(leaked))


if __name__ == "__main__":
    unittest.main()
