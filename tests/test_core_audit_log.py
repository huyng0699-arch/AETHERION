"""Tests for Q-0042 auditable record changes."""

from pathlib import Path
import tempfile
import unittest

from aetherion_server.audit_log import AuditLogStore


class AuditLogTests(unittest.TestCase):
    def test_logs_actor_and_previous_metadata_for_observation_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "audit.sqlite3"
            audit = AuditLogStore(db)

            entry = audit.record_change(
                observation_id=17,
                actor_id="engineer:alex",
                reason="Correct sensor calibration offset",
                previous_metadata={"unit": "ppm", "quality": "UNVERIFIED", "value": 420.0},
                new_metadata={"unit": "ppm", "quality": "READY", "value": 415.0},
            )
            self.assertEqual(entry["actor_id"], "engineer:alex")

            history = audit.list_changes(observation_id=17)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["previous_metadata"]["value"], 420.0)
            self.assertEqual(history[0]["new_metadata"]["value"], 415.0)
            self.assertEqual(history[0]["reason"], "Correct sensor calibration offset")

    def test_missing_actor_reason_or_previous_metadata_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "audit_bad.sqlite3"
            audit = AuditLogStore(db)
            with self.assertRaises(ValueError):
                audit.record_change(
                    observation_id=17,
                    actor_id="",
                    reason="fix",
                    previous_metadata={"value": 1},
                    new_metadata={"value": 2},
                )
            with self.assertRaises(ValueError):
                audit.record_change(
                    observation_id=17,
                    actor_id="engineer:alex",
                    reason="fix",
                    previous_metadata={},
                    new_metadata={"value": 2},
                )


if __name__ == "__main__":
    unittest.main()
