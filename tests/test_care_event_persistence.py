"""Tests for care event persistence across restarts (Q-0092)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SERVER_SRC = Path(__file__).resolve().parents[1] / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.care.episode import CareEpisodeStore
from aetherion_server.care.event_history import CareEventHistory


class TestCareEventPersistence(unittest.TestCase):
    def test_transitions_persist_with_episode_and_subject_id_across_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "care_restart.sqlite"
            store1 = CareEpisodeStore(db_path)
            ep = store1.start_episode(
                subject_id="CREW-07",
                actor_id="cmo-01",
                chief_concern="Post-EVA shoulder soreness",
                source="SELF_REPORT",
                data_state="READY",
                recorded_at="2026-11-14T08:00:00+00:00",
            )
            store1.advance_phase(
                ep["episode_id"],
                next_phase="EVALUATE",
                actor_id="cmo-01",
                source="CLINICAL_RULE_ENGINE",
                data_state="READY",
                summary="Evaluated range of motion; no red flags.",
                recorded_at="2026-11-14T08:05:00+00:00",
            )
            store1.advance_phase(
                ep["episode_id"],
                next_phase="ACT",
                actor_id="cmo-01",
                source="CREW_ACTION",
                data_state="READY",
                summary="Rest and cold compress applied.",
                recorded_at="2026-11-14T08:10:00+00:00",
            )
            del store1

            # Simulate process restart with new instances on same SQLite DB
            history = CareEventHistory(db_path)
            episodes = history.list_episodes_for_subject("CREW-07")
            self.assertEqual(len(episodes), 1)
            self.assertEqual(episodes[0]["episode_id"], ep["episode_id"])
            self.assertEqual(episodes[0]["current_phase"], "ACT")

            transitions = history.list_subject_transitions("CREW-07", episode_id=ep["episode_id"])
            self.assertEqual([t["phase"] for t in transitions], ["GATHER", "EVALUATE", "ACT"])
            self.assertTrue(all(t["subject_id"] == "CREW-07" for t in transitions))
            self.assertTrue(all(t["episode_id"] == ep["episode_id"] for t in transitions))

    def test_negative_blank_subject_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            history = CareEventHistory(Path(tmpdir) / "care_neg.sqlite")
            with self.assertRaises(ValueError):
                history.list_subject_transitions("   ")
            with self.assertRaises(ValueError):
                history.list_episodes_for_subject("")


if __name__ == "__main__":
    unittest.main()
