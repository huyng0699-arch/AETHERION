"""Q-0089 selected subject must match an authorized server response.

All identifiers and observations here are synthetic engineering fixtures.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps/desktop/src"))
from aetherion_desktop.features.personal.subject_selection_guard import (
    confirm_subject_from_authorized_response as check,
)


def payload(subject="CREW-7", rows=None):
    return {"subject_id": subject, "observations": rows if rows is not None else
            [{"subject_id": subject}]}


class ExactSubjectGuardTests(unittest.TestCase):
    def test_matching_authenticated_subject(self):
        result = check("CREW-7", "token", 200, payload())
        self.assertTrue(result.can_open)
        self.assertEqual(result.subject_id, "CREW-7")
        self.assertEqual(result.record_count, 1)

    def test_no_data_is_authorized_but_not_a_health_status(self):
        result = check("CREW-7", "token", 200, payload(rows=[]))
        self.assertEqual((result.status, result.record_count), ("NO_DATA", 0))

    def test_mismatched_server_subject_never_falls_back(self):
        result = check("CREW-8", "token", 200, payload("CREW-7"))
        self.assertEqual((result.status, result.subject_id), ("DENIED", None))

    def test_one_mixed_subject_record_fails_closed(self):
        result = check("CREW-7", "token", 200,
                       payload(rows=[{"subject_id": "CREW-7"},
                                     {"subject_id": "CREW-8"}]))
        self.assertEqual((result.status, result.record_count), ("ERROR", 0))

    def test_denied_and_offline_cannot_select_anyone(self):
        for code in (401, 403, None):
            with self.subTest(code=code):
                self.assertFalse(check("CREW-7", "token", code, payload()).can_open)

    def test_missing_token_and_empty_subject_are_denied(self):
        for subject, token in (("CREW-7", ""), ("", "token"),
                               ("CREW-7", "bad\nheader")):
            with self.subTest(subject=subject):
                self.assertEqual(check(subject, token, 200, payload()).status, "DENIED")

    def test_invisible_subject_suffix_does_not_select_default(self):
        result = check("CREW-7\u200b", "token", 200, payload())
        self.assertFalse(result.can_open)
        self.assertIsNone(result.subject_id)

    def test_other_error_and_malformed_response_are_not_authorization(self):
        self.assertEqual(check("CREW-7", "token", 500, payload()).status, "ERROR")
        self.assertEqual(check("CREW-7", "token", 200, {}).status, "DENIED")
        self.assertEqual(check("CREW-7", "token", 200,
                               {"subject_id": "CREW-7", "observations": "fake"}).status, "ERROR")


if __name__ == "__main__":
    unittest.main()
