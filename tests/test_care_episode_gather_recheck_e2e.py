"""E2E test for Q-0246: Care episode GATHER -> EVALUATE -> ACT -> RECHECK -> CLOSED across SQLite restart."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
for p in (str(REPO_ROOT), str(SERVER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from apps.server.src.aetherion_server.care.episode import (  # noqa: E402
    CareEpisodeStore,
    CareEpisodeTransitionError,
)


class CareEpisodeGatherRecheckE2ETests(unittest.TestCase):
    def test_full_gather_to_recheck_transitions_persist_across_sqlite_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "care_e2e.sqlite"
            store1 = CareEpisodeStore(db_path)

            ep = store1.start_episode(
                subject_id="CREW-01",
                actor_id="cmo-01",
                chief_concern="Post-EVA dizziness and mild nausea",
                source="symptom_intake",
                unit="episode",
                data_state="READY",
                recorded_at="2026-11-14T09:00:00+00:00",
                payload={"symptom": "Dizziness"},
            )
            episode_id = ep["episode_id"]
            self.assertEqual(ep["current_phase"], "GATHER")
            self.assertEqual(ep["subject_id"], "CREW-01")

            # Invalid skip GATHER -> ACT must be rejected
            with self.assertRaises(CareEpisodeTransitionError):
                store1.advance_phase(
                    episode_id,
                    next_phase="ACT",
                    actor_id="cmo-01",
                    source="manual",
                    summary="Skip evaluate",
                    recorded_at="2026-11-14T09:01:00+00:00",
                )

            store1.advance_phase(
                episode_id,
                next_phase="EVALUATE",
                actor_id="cmo-01",
                source="cliff_reference",
                summary="Reviewed CLIFF-062 motion sickness & orthostatic checks",
                recorded_at="2026-11-14T09:02:00+00:00",
            )
            store1.advance_phase(
                episode_id,
                next_phase="ACT",
                actor_id="cmo-01",
                source="human_clinician",
                summary="Oral hydration and seated rest",
                recorded_at="2026-11-14T09:05:00+00:00",
                human_confirmed=True,
            )
            store1.advance_phase(
                episode_id,
                next_phase="RECHECK",
                actor_id="cmo-01",
                source="vital_recheck",
                summary="Symptoms improved; vitals stable",
                recorded_at="2026-11-14T09:20:00+00:00",
            )
            store1.advance_phase(
                episode_id,
                next_phase="CLOSED",
                actor_id="cmo-01",
                source="human_clinician",
                summary="Episode resolved and closed",
                recorded_at="2026-11-14T09:30:00+00:00",
                human_confirmed=True,
            )

            # Simulate process/SQLite restart with a new CareEpisodeStore instance
            del store1
            store2 = CareEpisodeStore(db_path)
            reloaded = store2.get_episode(episode_id)
            self.assertEqual(reloaded["subject_id"], "CREW-01")
            self.assertEqual(reloaded["current_phase"], "CLOSED")
            self.assertEqual(
                [ev["phase"] for ev in reloaded["events"]],
                ["GATHER", "EVALUATE", "ACT", "RECHECK", "CLOSED"],
            )
            self.assertTrue(all(ev["recorded_at_utc"].endswith("+00:00") for ev in reloaded["events"]))


if __name__ == "__main__":
    unittest.main()
