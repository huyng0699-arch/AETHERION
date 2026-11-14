import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.i18n import SAFETY_COPY, get_localized_safety_notice


class GuideI18nTests(unittest.TestCase):
    def test_all_safety_keys_have_en_and_vi_with_identical_source_url(self) -> None:
        for key in SAFETY_COPY:
            en = get_localized_safety_notice(key, "en")
            vi = get_localized_safety_notice(key, "vi")
            self.assertEqual(en["source_url"], vi["source_url"])
            self.assertTrue(en["source_url"].startswith("https://"))
            self.assertNotEqual(en["text"], vi["text"])
            self.assertFalse(vi["fallback_used"])

    def test_unknown_language_falls_back_to_english_without_losing_link(self) -> None:
        res = get_localized_safety_notice("no_data_not_healthy", "fr")
        self.assertEqual(res["lang"], "en")
        self.assertTrue(res["fallback_used"])
        self.assertTrue(res["source_url"].startswith("https://"))


if __name__ == "__main__":
    unittest.main()
