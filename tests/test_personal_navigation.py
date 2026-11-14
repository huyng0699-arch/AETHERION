"""Focused validation of explicit Mission-to-Personal identity transfer."""
import unittest

from aetherion_desktop.features.personal.authorized_today import checked_personal_handoff


class PersonalHandoffTests(unittest.TestCase):
    def test_exact_identity_preserved(self):
        subject, token = checked_personal_handoff("  CREW-02  ", "session-value")
        self.assertEqual((subject, token), ("CREW-02", "session-value"))

    def test_requires_identity_and_token(self):
        for subject, token in [("", "token"), ("CREW-02", ""), ("CREW\nB", "token")]:
            with self.subTest(subject=repr(subject)):
                with self.assertRaises(ValueError):
                    checked_personal_handoff(subject, token)

    def test_rejects_newlines_in_auth_token(self):
        with self.assertRaises(ValueError):
            checked_personal_handoff("CREW-02", "token\r\nInvalid: yes")


if __name__ == "__main__":
    unittest.main()
