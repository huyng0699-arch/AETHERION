"""Tests actual SQLite behavior; no synthetic data is shown in the app UI."""

import tempfile
from pathlib import Path
import unittest

from aetherion_server.store import add_observation, list_observations


class StoreTests(unittest.TestCase):
    def test_persist_and_filter_by_subject(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "observations.sqlite3"
            item = {
                "subject_id": "ENGINEERING-A",
                "metric": "heart_rate",
                "value": 72.0,
                "unit": "beats/min",
                "source": "manual_software_test",
                "observed_at": "2026-11-14T09:00:00+07:00",
            }
            observation_id = add_observation(db, item)
            self.assertGreater(observation_id, 0)
            matching = list_observations(db, "ENGINEERING-A")
            other = list_observations(db, "ENGINEERING-B")
            self.assertEqual(len(matching), 1)
            self.assertEqual(matching[0]["value"], 72.0)
            self.assertEqual(matching[0]["source"], "manual_software_test")
            self.assertEqual(other, [])
            self.assertTrue(db.exists())


if __name__ == "__main__":
    unittest.main()
