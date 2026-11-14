"""Tests for direct witness incident logging store (Q-0167)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SERVER_SRC = Path(__file__).resolve().parents[1] / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.safety.witness_log import WitnessIncidentStore


class TestSafetyWitnessLog(unittest.TestCase):
    def test_witnessed_nonresponse_persists_with_subject_and_timestamp(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "witness.sqlite"
            store = WitnessIncidentStore(db_path)
            inc = store.log_witnessed_nonresponse(
                subject_id="CREW-04",
                witness_id="CREW-02",
                observed_at="2026-11-14T09:15:00+00:00",
                location="Airlock",
                circumstances="Crew member did not respond to verbal call during suit doffing.",
                telemetry_state="OFFLINE",
            )
            self.assertEqual(inc["source"], "WITNESS_REPORT")
            self.assertEqual(inc["subject_id"], "CREW-04")
            self.assertEqual(inc["witness_id"], "CREW-02")
            self.assertEqual(inc["telemetry_state"], "OFFLINE")
            self.assertEqual(inc["response_status"], "LOGGED_WITNESS_REPORT")

            # Verify persistence across reopen
            reopened = WitnessIncidentStore(db_path)
            items = reopened.list_incidents(subject_id="CREW-04")
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["incident_id"], inc["incident_id"])

    def test_negative_self_witness_and_naive_timestamp_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = WitnessIncidentStore(Path(tmpdir) / "witness_neg.sqlite")
            with self.assertRaises(ValueError):
                store.log_witnessed_nonresponse(
                    subject_id="CREW-04",
                    witness_id="CREW-04",
                    observed_at="2026-11-14T09:15:00+00:00",
                    circumstances="Self witness should fail",
                )
            with self.assertRaises(ValueError):
                store.log_witnessed_nonresponse(
                    subject_id="CREW-04",
                    witness_id="CREW-02",
                    observed_at="2026-11-14T09:15:00",
                    circumstances="Naive timestamp should fail",
                )


if __name__ == "__main__":
    unittest.main()
