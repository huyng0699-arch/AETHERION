"""Deterministic tests for Q-0172 (assistance follow-up care episode linkage)."""

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


class SafetyCareFollowupTests(unittest.TestCase):
    def test_acknowledged_incident_opens_linked_care_episode_and_preserves_history(self) -> None:
        now = datetime(2026, 11, 14, 9, 24, tzinfo=timezone.utc)
        reg = IncidentRegistry()
        inc = reg.create_incident(
            incident_id="inc-100",
            subject_id="crew-03",
            mission_id="lunar-hab-1",
            incident_type="NEED_HELP_NOW",
            source="desktop_button",
            now=now,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            store = CareEpisodeStore(Path(tmpdir) / "care.sqlite")
            with self.assertRaises(ValueError):
                open_followup_care_episode(inc, store, actor_id="cmo-01", now=now)

            reg.acknowledge_incident(
                incident_id="inc-100",
                acknowledged_by="cmo-01",
                event_id="ev-ack-100",
                note="Responding with med kit",
                now=now,
            )
            link = open_followup_care_episode(
                inc,
                store,
                actor_id="cmo-01",
                chief_concern="Acute dizziness post-EVA",
                now=now,
            )
            self.assertEqual(link.incident_id, "inc-100")
            self.assertEqual(link.subject_id, "crew-03")
            self.assertEqual(link.preserved_event_count, 1)
            self.assertEqual(inc.events[-1].event_kind, "CARE_FOLLOWUP_OPENED")

            conn = sqlite3.connect(Path(tmpdir) / "care.sqlite")
            try:
                row = conn.execute(
                    "SELECT payload_json, source FROM care_episode_events WHERE episode_id=?",
                    (link.episode_id,),
                ).fetchone()
                self.assertIsNotNone(row)
                payload = json.loads(row[0])
                self.assertEqual(payload["incident_id"], "inc-100")
                self.assertEqual(len(payload["incident_event_history"]), 1)
                self.assertEqual(row[1], "safety_incident:inc-100")
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
