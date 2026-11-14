"""Contract tests for Q-0026 scientific citation schema."""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "packages" / "contracts" / "scientific_citation.schema.json"


def validate_citation(citation: dict, schema: dict) -> None:
    required = set(schema["required"])
    missing = required - set(citation.keys())
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    extra = set(citation.keys()) - set(schema["properties"].keys())
    if extra:
        raise ValueError(f"unexpected fields: {sorted(extra)}")

    if not str(citation["publisher"]).strip():
        raise ValueError("publisher must be non-empty")
    if not re.match(r"^https?://\S+$", str(citation["source_url"])):
        raise ValueError("source_url must be a valid http/https URL")
    if citation["license_status"] not in schema["properties"]["license_status"]["enum"]:
        raise ValueError(f"invalid license_status: {citation['license_status']}")
    if not isinstance(citation["verified"], bool):
        raise ValueError("verified must be boolean")
    if citation["is_live_crew_telemetry"] is not False:
        raise ValueError("scientific citations must have is_live_crew_telemetry=false")
    if "sha256" in citation and not re.match(r"^[a-f0-9]{64}$", citation["sha256"]):
        raise ValueError("sha256 must be 64 lowercase hex characters")


class ScientificCitationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_valid_nasa_citation_passes(self) -> None:
        citation = {
            "citation_id": "NASA-STD-3001-V2",
            "title": "NASA Space Flight Human-System Standard Volume 2",
            "publisher": "NASA",
            "source_url": "https://www.nasa.gov/reference/nasa-std-3001-volume-2/",
            "license_status": "PUBLIC_DOMAIN",
            "verified": True,
            "sha256": "a" * 64,
            "is_live_crew_telemetry": False,
        }
        validate_citation(citation, self.schema)

    def test_missing_url_invalid_license_or_live_telemetry_flag_rejected(self) -> None:
        bad_url = {
            "citation_id": "BAD-1",
            "title": "Sample",
            "publisher": "NASA",
            "source_url": "not-a-url",
            "license_status": "PUBLIC_DOMAIN",
            "verified": False,
            "is_live_crew_telemetry": False,
        }
        with self.assertRaises(ValueError):
            validate_citation(bad_url, self.schema)

        bad_live = dict(bad_url)
        bad_live["source_url"] = "https://example.org/doc"
        bad_live["is_live_crew_telemetry"] = True
        with self.assertRaises(ValueError):
            validate_citation(bad_live, self.schema)


if __name__ == "__main__":
    unittest.main()
