import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.consent_log import GuideConsentLog


class GuideConsentLogTests(unittest.TestCase):
    def test_sensitive_input_not_retained_without_explicit_consent(self) -> None:
        log = GuideConsentLog()
        res = log.record_interaction(
            subject_id="crew-01",
            user_input="Private symptom note: chest tightness",
            is_sensitive=True,
            explicit_retention_consent=False,
        )
        self.assertFalse(res["retained"])
        self.assertTrue(res["redacted"])
        self.assertEqual(res["input_text"], "[REDACTED_NO_CONSENT]")
        self.assertEqual(log.list_retained(), [])

    def test_sensitive_input_retained_only_with_explicit_consent(self) -> None:
        log = GuideConsentLog()
        res = log.record_interaction(
            subject_id="crew-01",
            user_input="Authorized care note",
            is_sensitive=True,
            explicit_retention_consent=True,
        )
        self.assertTrue(res["retained"])
        self.assertFalse(res["redacted"])
        self.assertEqual(len(log.list_retained()), 1)


if __name__ == "__main__":
    unittest.main()
