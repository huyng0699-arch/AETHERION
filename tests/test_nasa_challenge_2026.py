from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "knowledge" / "nasa" / "challenge_2026.json"
MD_PATH = ROOT / "knowledge" / "nasa" / "challenge_2026.md"


class TestNasaChallenge2026(unittest.TestCase):
    def test_json_artifact_exists_and_has_provenance(self) -> None:
        self.assertTrue(JSON_PATH.is_file(), f"Missing {JSON_PATH}")
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

        provenance = data["provenance"]
        self.assertEqual(
            provenance["source_url"],
            "https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/",
        )
        self.assertEqual(provenance["verification_status"], "VERIFIED_OFFICIAL_SOURCE")
        self.assertTrue(provenance["retrieved_at_utc"].endswith("Z"))
        self.assertTrue(provenance["limitations"], "Must explicitly state limitations")

    def test_five_hazards_and_indicators_present(self) -> None:
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        challenge = data["challenge"]

        self.assertEqual(
            challenge["title"],
            "Create Health Monitoring Software for Astronauts on Space Missions",
        )
        hazards = [h["id"] for h in challenge["five_hazards"]]
        self.assertEqual(
            hazards,
            [
                "space_radiation",
                "isolation_and_confinement",
                "distance_from_earth",
                "gravity_fields",
                "hostile_closed_environments",
            ],
        )
        indicators = {item["name"] for item in challenge["example_health_indicators"]}
        self.assertTrue(
            {"blood_pressure", "heart_rate", "blood_sugar", "body_temperature", "daily_sleep_hours", "mood"}.issubset(
                indicators
            )
        )

    def test_evaluation_criteria_and_markdown_hash_match(self) -> None:
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            data["evaluation_emphasis"]["judging_criteria_equal_weight"],
            ["Impact", "Creativity", "Validity", "Relevance", "Presentation"],
        )

        self.assertTrue(MD_PATH.is_file(), f"Missing {MD_PATH}")
        md_text = MD_PATH.read_text(encoding="utf-8")
        digest = hashlib.sha256(JSON_PATH.read_bytes()).hexdigest()
        self.assertIn(digest, md_text)
        self.assertIn("https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/", md_text)


if __name__ == "__main__":
    unittest.main()
