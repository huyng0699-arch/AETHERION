from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAZARD_PATH = ROOT / "knowledge" / "nasa" / "hazards" / "hostile_closed_environment.json"


class TestNasaHazardHabitat(unittest.TestCase):
    def test_cabin_environment_and_personal_medical_scopes_are_disjoint(self) -> None:
        self.assertTrue(HAZARD_PATH.is_file(), f"Missing {HAZARD_PATH}")
        data = json.loads(HAZARD_PATH.read_text(encoding="utf-8"))

        self.assertEqual(data["hazard_id"], "hostile_closed_environments")
        self.assertFalse(data["is_live_telemetry"])
        sep = data["scope_separation"]
        self.assertEqual(sep["cabin_environmental_scope"]["scope"], "HABITAT")
        self.assertEqual(sep["personal_medical_scope"]["scope"], "PERSONAL")

        cabin_metrics = {m["metric"] for m in sep["cabin_environmental_scope"]["metrics"]}
        personal_metrics = {m["metric"] for m in sep["personal_medical_scope"]["metrics"]}
        self.assertTrue(cabin_metrics.isdisjoint(personal_metrics))
        self.assertIn("cabin_temperature_c", cabin_metrics)
        self.assertIn("body_temperature_c", personal_metrics)


if __name__ == "__main__":
    unittest.main()
