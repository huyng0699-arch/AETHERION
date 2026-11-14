"""Tests for stateful GATHER -> EVALUATE -> ACT -> RECHECK care episode model (Q-0091)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SERVER_SRC = Path(__file__).resolve().parents[1] / "apps" / "server" / "src"
if str(SERVER_SRC) not in sys.path:
    sys.path.insert(0, str(SERVER_SRC))

from aetherion_server.care.episode import CareEpisodeStore, CareEpisodeTransitionError


class TestCareEpisode(unittest.TestCase):
    def test_full_gather_evaluate_act_recheck_lifecycle_without_ai(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CareEpisodeStore(Path(tmpdir) / "care.sqlite")
            ep = store.start_episode(
                subject_id="crew-01",
                actor_id="cmo-01",
                chief_concern="Mild sinus pressure after EVA",
                source="SELF_REPORT",
                unit="symptom_scale",
                data_state="READY",
                recorded_at="2026-11-14T06:00:00+00:00",
                ai_assisted=False,
                human_confirmed=True,
            )
            self.assertEqual(ep["current_phase"], "GATHER")
            self.assertFalse(ep["ai_assisted"])

            ep = store.advance_phase(
                ep["episode_id"],
                next_phase="EVALUATE",
                actor_id="cmo-01",
                source="CLINICAL_RULE_ENGINE",
                data_state="NO_DATA",
                summary="No live otoscope telemetry attached; missing data is not unconsciousness.",
                recorded_at="2026-11-14T06:05:00+00:00",
            )
            self.assertEqual(ep["current_phase"], "EVALUATE")

            ep = store.advance_phase(
                ep["episode_id"],
                next_phase="ACT",
                actor_id="cmo-01",
                source="CREW_ACTION",
                data_state="READY",
                summary="Documented supportive hydration and scheduled recheck.",
                recorded_at="2026-11-14T06:10:00+00:00",
                human_confirmed=True,
            )
            self.assertEqual(ep["current_phase"], "ACT")

            ep = store.advance_phase(
                ep["episode_id"],
                next_phase="RECHECK",
                actor_id="cmo-01",
                source="SELF_REPORT",
                data_state="READY",
                summary="Symptoms improved on 30-minute recheck.",
                recorded_at="2026-11-14T06:40:00+00:00",
            )
            self.assertEqual(ep["current_phase"], "RECHECK")
            self.assertEqual([e["phase"] for e in ep["events"]], ["GATHER", "EVALUATE", "ACT", "RECHECK"])
            self.assertEqual(ep["events"][1]["data_state"], "NO_DATA")

    def test_negative_skipping_phase_and_unconfirmed_act_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CareEpisodeStore(Path(tmpdir) / "care_neg.sqlite")
            ep = store.start_episode(
                subject_id="crew-02",
                actor_id="cmo-01",
                chief_concern="Dizziness",
                source="SELF_REPORT",
                recorded_at="2026-11-14T06:00:00+00:00",
            )
            with self.assertRaises(CareEpisodeTransitionError):
                store.advance_phase(
                    ep["episode_id"],
                    next_phase="ACT",
                    actor_id="cmo-01",
                    source="CREW_ACTION",
                    summary="Attempted skip from GATHER to ACT",
                )

            store.advance_phase(
                ep["episode_id"],
                next_phase="EVALUATE",
                actor_id="cmo-01",
                source="CLINICAL_RULE_ENGINE",
                summary="Evaluated",
            )
            with self.assertRaises(CareEpisodeTransitionError):
                store.advance_phase(
                    ep["episode_id"],
                    next_phase="ACT",
                    actor_id="cmo-01",
                    source="CREW_ACTION",
                    summary="Attempted unconfirmed ACT",
                    human_confirmed=False,
                )


if __name__ == "__main__":
    unittest.main()
