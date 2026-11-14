from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_nasa_registry import DEFAULT_REGISTRY, validate_registry


class TestNasaSourceRegistry(unittest.TestCase):
    def test_repo_registry_passes_schema_and_sha256_checks(self) -> None:
        errors = validate_registry(DEFAULT_REGISTRY)
        self.assertEqual(errors, [], f"Registry validation errors: {errors}")

    def test_negative_hash_tampering_and_live_telemetry_flag_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sample = root / "sample.json"
            sample.write_text('{"ok": true}\n', encoding="utf-8")
            bad_registry = root / "bad_registry.json"
            bad_registry.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "updated_at_utc": "2026-11-14T03:52:00Z",
                        "items": [
                            {
                                "item_id": "bad-item",
                                "quest_id": "Q-0111",
                                "publisher": "NASA",
                                "source_uri": "https://osdr.nasa.gov/",
                                "retrieved_at_utc": "2026-11-14T03:52:00Z",
                                "local_path": "sample.json",
                                "sha256": "0" * 64,
                                "validation_state": "INVALID_STATE",
                                "is_live_telemetry": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            errors = validate_registry(bad_registry, root_dir=root)
            self.assertTrue(any("sha256 mismatch" in e for e in errors))
            self.assertTrue(any("invalid validation_state" in e for e in errors))
            self.assertTrue(any("is_live_telemetry must be false" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
