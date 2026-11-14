from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "knowledge" / "nasa" / "official_resources.json"
MD_PATH = ROOT / "knowledge" / "nasa" / "official_resources.md"


class TestNasaOfficialResources(unittest.TestCase):
    def test_resources_exist_with_provenance_and_no_live_telemetry_claim(self) -> None:
        self.assertTrue(JSON_PATH.is_file(), f"Missing {JSON_PATH}")
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

        resources = {r["resource_id"]: r for r in data["resources"]}
        self.assertTrue({"nasa-osdr", "nasa-nlsp", "nasa-hrp-hazards", "nasa-imm-cliff-119"}.issubset(resources))

        for rid, res in resources.items():
            self.assertTrue(res["source_url"].startswith("https://"), f"{rid} missing https source_url")
            self.assertTrue(res["retrieved_at_utc"].endswith("Z"), f"{rid} missing UTC timestamp")
            self.assertTrue(res["not_live_crew_telemetry"], f"{rid} must mark not_live_crew_telemetry=True")
            self.assertTrue(res["limitations"], f"{rid} must document limitations")

        # CliFF 119 must remain honestly marked as unimported until verified
        self.assertEqual(resources["nasa-imm-cliff-119"]["verification_status"], "LINKED_ONLY_UNIMPORTED")

    def test_markdown_matches_json_sha256(self) -> None:
        self.assertTrue(MD_PATH.is_file(), f"Missing {MD_PATH}")
        md_text = MD_PATH.read_text(encoding="utf-8")
        digest = hashlib.sha256(JSON_PATH.read_bytes()).hexdigest()
        self.assertIn(digest, md_text)
        self.assertIn("https://osdr.nasa.gov/", md_text)
        self.assertIn("https://www.nasa.gov/hrp/nlsp/", md_text)


if __name__ == "__main__":
    unittest.main()
