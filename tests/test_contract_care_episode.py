"""Contract tests for Q-0025 care episode GATHER->EVALUATE->ACT->RECHECK schema."""

from datetime import datetime
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "packages" / "contracts" / "care_episode.schema.json"


def validate_care_episode(record: dict, schema: dict) -> None:
    required = set(schema["required"])
    missing = required - set(record.keys())
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    extra = set(record.keys()) - set(schema["properties"].keys())
    if extra:
        raise ValueError(f"unexpected fields: {sorted(extra)}")

    if record["scope"] not in schema["properties"]["scope"]["enum"]:
        raise ValueError(f"invalid scope: {record['scope']}")
    if record["deterministic_safety_active"] is not True:
        raise ValueError("deterministic_safety_active must remain true")
    if not str(record["human_actor_id"]).strip():
        raise ValueError("human_actor_id must be non-empty")
    if not record["source_observation_ids"]:
        raise ValueError("source_observation_ids must reference at least one observation ID")

    phase = record["phase"]
    prev = record["previous_phase"]
    transitions = schema["x-care-transitions"]
    if phase not in transitions:
        raise ValueError(f"unknown phase: {phase}")
    if prev not in transitions[phase]["from"]:
        raise ValueError(f"invalid transition {prev!r} -> {phase!r}")

    dt = datetime.fromisoformat(record["updated_at"])
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("updated_at must include timezone offset")


class CareEpisodeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_defines_gather_evaluate_act_recheck_flow(self) -> None:
        self.assertEqual(
            self.schema["properties"]["phase"]["enum"],
            ["GATHER", "EVALUATE", "ACT", "RECHECK", "CLOSED"],
        )
        self.assertEqual(
            self.schema["x-care-transitions"]["GATHER"]["to"],
            ["EVALUATE"],
        )
        self.assertEqual(
            self.schema["x-care-transitions"]["ACT"]["to"],
            ["RECHECK"],
        )

    def test_valid_care_episode_transitions_pass(self) -> None:
        steps = [
            ("GATHER", None, [1]),
            ("EVALUATE", "GATHER", [1, 2]),
            ("ACT", "EVALUATE", [1, 2]),
            ("RECHECK", "ACT", [1, 2, 3]),
            ("CLOSED", "RECHECK", [1, 2, 3]),
        ]
        for phase, prev, obs_ids in steps:
            validate_care_episode(
                {
                    "episode_id": "ep-crew1-001",
                    "subject_id": "CREW-1",
                    "scope": "CREW",
                    "phase": phase,
                    "previous_phase": prev,
                    "source_observation_ids": obs_ids,
                    "human_actor_id": "crew:CREW-1",
                    "deterministic_safety_active": True,
                    "ai_assisted": False,
                    "updated_at": "2026-11-14T05:08:00+00:00",
                },
                self.schema,
            )

    def test_invalid_transitions_and_missing_observation_ids_rejected(self) -> None:
        skip_evaluate = {
            "episode_id": "ep-crew1-bad",
            "subject_id": "CREW-1",
            "scope": "CREW",
            "phase": "ACT",
            "previous_phase": "GATHER",
            "source_observation_ids": [1],
            "human_actor_id": "crew:CREW-1",
            "deterministic_safety_active": True,
            "ai_assisted": False,
            "updated_at": "2026-11-14T05:08:00+00:00",
        }
        with self.assertRaises(ValueError):
            validate_care_episode(skip_evaluate, self.schema)

        empty_obs = dict(skip_evaluate)
        empty_obs["phase"] = "GATHER"
        empty_obs["previous_phase"] = None
        empty_obs["source_observation_ids"] = []
        with self.assertRaises(ValueError):
            validate_care_episode(empty_obs, self.schema)

        safety_disabled = dict(skip_evaluate)
        safety_disabled["phase"] = "GATHER"
        safety_disabled["previous_phase"] = None
        safety_disabled["deterministic_safety_active"] = False
        with self.assertRaises(ValueError):
            validate_care_episode(safety_disabled, self.schema)


if __name__ == "__main__":
    unittest.main()
