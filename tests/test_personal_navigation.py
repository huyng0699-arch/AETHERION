"""Focused validation of explicit Mission-to-Personal identity transfer."""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "apps/desktop/src/aetherion_desktop/features/personal/identity.py"
)
spec = importlib.util.spec_from_file_location("aetherion_personal_identity", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
checked_personal_handoff = module.checked_personal_handoff


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
