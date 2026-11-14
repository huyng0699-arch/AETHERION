import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.symptom_disclosure import build_guide_session


class GuideSymptomDisclosureTests(unittest.TestCase):
    def test_healthy_navigation_works_with_no_symptoms(self) -> None:
        session = build_guide_session(disclosed_symptoms=None, query="OSD-575", repo_root=ROOT)
        self.assertFalse(session["symptom_required"])
        self.assertFalse(session["navigation_blocked"])
        self.assertTrue(session["healthy_navigation_available"])
        self.assertEqual(session["mode"], "HEALTHY_EXPLORATION")
        self.assertGreaterEqual(session["search_results"]["count"], 1)

    def test_optional_symptom_disclosure_enriches_without_blocking(self) -> None:
        session = build_guide_session(
            disclosed_symptoms=["sleep disruption during isolation"],
            query="",
            repo_root=ROOT,
        )
        self.assertFalse(session["symptom_required"])
        self.assertFalse(session["navigation_blocked"])
        self.assertEqual(session["mode"], "SYMPTOM_CONTEXT")
        self.assertFalse(session["diagnosis_produced"])
        self.assertEqual(session["suggested_hazards"][0]["hazard_id"], "isolation_and_confinement")


if __name__ == "__main__":
    unittest.main()
