from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAZARD_PATH = ROOT / "knowledge" / "nasa" / "hazards" / "isolation_confinement.json"


class TestNasaHazardIsolation(unittest.TestCase):
    def test_isolation_module_avoids_clinical_overclaim(self) -> None:
        self.assertTrue(HAZARD_PATH.is_file(), f"Missing {HAZARD_PATH}")
        data = json.loads(HAZARD_PATH.read_text(encoding="utf-8"))

        self.assertEqual(data["hazard_id"], "isolation_and_confinement")
        self.assertFalse(data["is_live_telemetry"])
        metrics = {item["metric"] for item in data["behavioral_indicators_without_clinical_overclaim"]}
        self.assertTrue({"daily_sleep_hours", "mood_self_report"}.issubset(metrics))
        self.assertIn("NO_DATA", json.dumps(data))
        self.assertTrue(data["limitations"])


if __name__ == "__main__":
    unittest.main()
