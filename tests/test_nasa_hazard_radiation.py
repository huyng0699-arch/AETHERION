from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAZARD_PATH = ROOT / "knowledge" / "nasa" / "hazards" / "space_radiation.json"


class TestNasaHazardRadiation(unittest.TestCase):
    def test_radiation_module_has_primary_sources_and_organ_systems(self) -> None:
        self.assertTrue(HAZARD_PATH.is_file(), f"Missing {HAZARD_PATH}")
        data = json.loads(HAZARD_PATH.read_text(encoding="utf-8"))

        self.assertEqual(data["hazard_id"], "space_radiation")
        self.assertFalse(data["is_live_telemetry"])
        source_ids = {s["source_id"] for s in data["primary_sources"]}
        self.assertTrue({"nasa-hrp", "OSD-431"}.issubset(source_ids))

        for sys_item in data["affected_organ_systems"]:
            self.assertTrue(sys_item["source_ids"], f"{sys_item['system_id']} must cite primary source_ids")
            for sid in sys_item["source_ids"]:
                self.assertIn(sid, source_ids)

        self.assertTrue(data["limitations"])


if __name__ == "__main__":
    unittest.main()
