import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.safety_escalation import evaluate_safety_escalation


class GuideSafetyEscalationTests(unittest.TestCase):
    def test_assistance_entry_operable_when_ai_disabled_and_offline(self) -> None:
        res = evaluate_safety_escalation("", ai_enabled=False, ai_reachable=False)
        self.assertTrue(res["assistance_entry_available"])
        self.assertEqual(res["assistance_route"], "safety/assistance")
        self.assertFalse(res["ai_required"])
        self.assertFalse(res["escalation_recommended"])
        self.assertFalse(res["claimed_dispatch"])

    def test_red_flag_escalation_works_without_ai(self) -> None:
        res = evaluate_safety_escalation(
            "Crewmate reports chest pain and difficulty breathing",
            ai_enabled=False,
            ai_reachable=False,
        )
        self.assertTrue(res["assistance_entry_available"])
        self.assertTrue(res["escalation_recommended"])
        self.assertIn("chest pain", res["matched_red_flags"])
        self.assertFalse(res["claimed_diagnosis"])


if __name__ == "__main__":
    unittest.main()
