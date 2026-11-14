"""End-to-end assistance acceptance test for Q-0180:
Witness report -> Safety incident -> ACK -> Linked Care episode -> SQLite restart.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
for p in (str(REPO_ROOT), str(SERVER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from apps.server.src.aetherion_server.care.episode import CareEpisodeStore  # noqa: E402
from apps.server.src.aetherion_server.safety.care_followup import open_followup_care_episode  # noqa: E402
from apps.server.src.aetherion_server.safety.incidents import IncidentRegistry  # noqa: E402
from apps.server.src.aetherion_server.safety.witness_log import WitnessIncidentStore  # noqa: E402


class TestAssistanceEndToEndRestart(unittest.TestCase):
    def test_witness_report_to_ack_to_care_persists_across_db_restart(self) -> None:
        now = datetime(2026, 11, 14, 14, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as tmpdir:
            witness_db = Path(tmpdir) / "witness.sqlite"
            care_db = Path(tmpdir) / "care.sqlite"

            witness_store = WitnessIncidentStore(witness_db)
            witness_record = witness_store.log_witnessed_nonresponse(
                subject_id="crew-04",
                witness_id="crew-01",
                observed_at=now.isoformat(),
                circumstances="No response on EVA comm check",
                location="Airlock-2",
                telemetry_state="NO_DATA",
            )
            self.assertEqual(witness_record["source"], "WITNESS_REPORT")
            self.assertEqual(witness_record["telemetry_state"], "NO_DATA")

            registry = IncidentRegistry()
            incident = registry.create_incident(
                incident_id=witness_record["incident_id"],
                subject_id="crew-04",
                mission_id="lunar-hab-1",
                incident_type="WITNESSED_NONRESPONSE",
                source="WITNESS_REPORT",
                now=now,
            )

            registry.acknowledge_incident(
                incident_id=incident.incident_id,
                acknowledged_by="cmo-01",
                event_id="ev-ack-0180",
                note="CMO en route to Airlock-2",
                now=now,
            )

            care_store = CareEpisodeStore(care_db)
            link = open_followup_care_episode(
                incident,
                care_store,
                actor_id="cmo-01",
                chief_concern="Witnessed nonresponse follow-up",
                now=now,
            )
            self.assertEqual(link.incident_id, witness_record["incident_id"])
            self.assertEqual(link.subject_id, "crew-04")
            self.assertEqual(link.preserved_event_count, 1)

            # Simulate database/process restart by dropping in-memory stores and reopening from SQLite.
            del witness_store
            del care_store

            reopened_witness = WitnessIncidentStore(witness_db)
            persisted_witness = reopened_witness.get_incident(witness_record["incident_id"])
            self.assertEqual(persisted_witness["subject_id"], "crew-04")
            self.assertEqual(persisted_witness["witness_id"], "crew-01")
            self.assertEqual(persisted_witness["telemetry_state"], "NO_DATA")
            self.assertEqual(persisted_witness["response_status"], "LOGGED_WITNESS_REPORT")

            reopened_care = CareEpisodeStore(care_db)
            persisted_episode = reopened_care.get_episode(link.episode_id)
            self.assertEqual(persisted_episode["episode_id"], link.episode_id)
            self.assertEqual(persisted_episode["subject_id"], "crew-04")

            conn = sqlite3.connect(care_db)
            try:
                row = conn.execute(
                    "SELECT source, payload_json FROM care_episode_events WHERE episode_id = ?",
                    (link.episode_id,),
                ).fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], f"safety_incident:{witness_record['incident_id']}")
                payload = json.loads(row[1])
                self.assertEqual(payload["incident_id"], witness_record["incident_id"])
                self.assertEqual(payload["acknowledged_by"], "cmo-01")
                self.assertEqual(len(payload["incident_event_history"]), 1)
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
