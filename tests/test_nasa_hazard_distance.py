from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAZARD_PATH = ROOT / "knowledge" / "nasa" / "hazards" / "distance_from_earth.json"


class TestNasaHazardDistance(unittest.TestCase):
    def test_distance_module_documents_delay_and_offline_autonomy(self) -> None:
        self.assertTrue(HAZARD_PATH.is_file(), f"Missing {HAZARD_PATH}")
        data = json.loads(HAZARD_PATH.read_text(encoding="utf-8"))

        self.assertEqual(data["hazard_id"], "distance_from_earth")
        self.assertFalse(data["is_live_telemetry"])
        constraints = data["communication_delay_and_autonomy_constraints"]
        self.assertTrue(constraints["source_ids"])
        self.assertIn("OFFLINE", json.dumps(constraints))
        self.assertTrue(data["limitations"])


if __name__ == "__main__":
    unittest.main()
