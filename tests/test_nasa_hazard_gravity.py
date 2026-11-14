from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAZARD_PATH = ROOT / "knowledge" / "nasa" / "hazards" / "altered_gravity.json"


class TestNasaHazardGravity(unittest.TestCase):
    def test_gravity_module_covers_musculoskeletal_and_cardiovascular(self) -> None:
        self.assertTrue(HAZARD_PATH.is_file(), f"Missing {HAZARD_PATH}")
        data = json.loads(HAZARD_PATH.read_text(encoding="utf-8"))

        self.assertEqual(data["hazard_id"], "gravity_fields")
        self.assertFalse(data["is_live_telemetry"])
        systems = {c["system_id"] for c in data["consequences"]}
        self.assertEqual(systems, {"musculoskeletal", "cardiovascular"})
        source_ids = {s["source_id"] for s in data["primary_sources"]}
        for item in data["consequences"]:
            for sid in item["source_ids"]:
                self.assertIn(sid, source_ids)


if __name__ == "__main__":
    unittest.main()
