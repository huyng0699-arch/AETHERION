"""Tests for Q-0040 event replay and duplicate control."""

from pathlib import Path
import tempfile
import unittest

from aetherion_server.replay_guard import EventReplayGuard


class ReplayGuardTests(unittest.TestCase):
    def test_replaying_event_produces_no_duplicate_row_or_alert(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "replay.sqlite3"
            guard = EventReplayGuard(db)
            payload = {"subject_id": "CREW-1", "metric": "heart_rate", "value": 122}

            first = guard.process_event(
                stream_name="observations",
                event_uid="evt-hr-001",
                payload=payload,
                emit_alert=True,
            )
            self.assertFalse(first.replayed)
            self.assertTrue(first.alert_emitted)

            replay = guard.process_event(
                stream_name="observations",
                event_uid="evt-hr-001",
                payload=payload,
                emit_alert=True,
            )
            self.assertTrue(replay.replayed)
            self.assertFalse(replay.alert_emitted)
            self.assertEqual(replay.row_id, first.row_id)
            self.assertEqual(guard.count_events(stream_name="observations"), 1)

    def test_conflicting_payload_for_same_event_uid_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "replay_conflict.sqlite3"
            guard = EventReplayGuard(db)
            guard.process_event(
                stream_name="observations",
                event_uid="evt-hr-002",
                payload={"value": 70},
                emit_alert=False,
            )
            with self.assertRaises(ValueError):
                guard.process_event(
                    stream_name="observations",
                    event_uid="evt-hr-002",
                    payload={"value": 99},
                    emit_alert=False,
                )


if __name__ == "__main__":
    unittest.main()
