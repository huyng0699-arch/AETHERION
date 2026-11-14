import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.hazard_router import load_nasa_hazards, route_question_to_hazard


class GuideHazardRouterTests(unittest.TestCase):
    def test_all_five_nasa_hazards_are_loaded(self) -> None:
        hazards = load_nasa_hazards(repo_root=ROOT)
        self.assertEqual(
            set(hazards.keys()),
            {
                "space_radiation",
                "isolation_and_confinement",
                "distance_from_earth",
                "gravity_fields",
                "hostile_closed_environments",
            },
        )

    def test_questions_route_to_matching_hazard_with_sources(self) -> None:
        cases = [
            ("How does space radiation affect DNA repair?", "space_radiation"),
            ("Why does microgravity cause bone and muscle loss?", "gravity_fields"),
            ("How does isolation impact circadian sleep?", "isolation_and_confinement"),
            ("What happens when communication distance delays resupply?", "distance_from_earth"),
            ("Why monitor cabin CO2 in a closed habitat?", "hostile_closed_environments"),
        ]
        for question, expected_id in cases:
            routed = route_question_to_hazard(question, repo_root=ROOT)
            self.assertEqual(routed["status"], "ROUTED")
            self.assertEqual(routed["hazard_id"], expected_id)
            self.assertEqual(routed["target_route"], f"explore/hazards/{expected_id}")
            self.assertGreater(len(routed["primary_sources"]), 0)
            self.assertFalse(routed["is_live_telemetry"])

    def test_unmatched_question_fails_closed(self) -> None:
        res = route_question_to_hazard("What is the price of coffee?", repo_root=ROOT)
        self.assertEqual(res["status"], "UNMATCHED")
        self.assertIsNone(res["target_route"])
        self.assertIsNone(res["hazard_id"])


if __name__ == "__main__":
    unittest.main()
