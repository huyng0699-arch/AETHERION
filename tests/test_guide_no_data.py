import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = ROOT / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.guide.no_data import explain_unknown_state


class GuideNoDataTests(unittest.TestCase):
    def test_missing_metrics_explain_unknown_without_diagnosis(self) -> None:
        res = explain_unknown_state(None, ["heart_rate", "radiation_dose_msv"])
        self.assertFalse(res["diagnosis_produced"])
        self.assertEqual(res["known_metrics"], [])
        self.assertEqual(len(res["unknown_metrics"]), 2)
        self.assertIn("no diagnosis produced", res["summary"])

    def test_stale_and_offline_metrics_are_flagged_unknown(self) -> None:
        res = explain_unknown_state(
            {
                "heart_rate": {"value": 70, "verification_state": "READY"},
                "spo2": {"value": 97, "verification_state": "STALE"},
                "cabin_co2": {"value": None, "verification_state": "OFFLINE"},
            },
            ["heart_rate", "spo2", "cabin_co2"],
        )
        self.assertFalse(res["diagnosis_produced"])
        self.assertEqual(res["known_metrics"], ["heart_rate"])
        self.assertEqual([u["metric"] for u in res["unknown_metrics"]], ["spo2", "cabin_co2"])


if __name__ == "__main__":
    unittest.main()
