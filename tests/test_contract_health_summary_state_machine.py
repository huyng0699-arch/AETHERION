"""Contract tests for Q-0027 health summary state machine."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "packages" / "contracts" / "health_summary_state_machine.schema.json"


def compute_summary_state(
    *,
    transport_connected: bool,
    backend_error: bool,
    observation_count: int,
    age_seconds: float | None,
    max_age_seconds: float,
) -> str:
    if not transport_connected:
        return "OFFLINE"
    if backend_error:
        return "ERROR"
    if observation_count == 0 or age_seconds is None:
        return "NO_DATA"
    if age_seconds > max_age_seconds:
        return "STALE"
    return "READY"


def validate_transition(prev_state: str | None, next_state: str, schema: dict) -> None:
    if prev_state is None:
        return
    allowed = schema["x-transitions"].get(prev_state, [])
    if next_state not in allowed:
        raise ValueError(f"ambiguous/disallowed transition {prev_state} -> {next_state}")


class HealthSummaryStateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_state_machine_precedence_is_unambiguous(self) -> None:
        self.assertEqual(
            self.schema["properties"]["state"]["enum"],
            ["READY", "NO_DATA", "STALE", "OFFLINE", "ERROR"],
        )
        self.assertEqual(
            compute_summary_state(
                transport_connected=False,
                backend_error=True,
                observation_count=5,
                age_seconds=10.0,
                max_age_seconds=300.0,
            ),
            "OFFLINE",
        )
        self.assertEqual(
            compute_summary_state(
                transport_connected=True,
                backend_error=True,
                observation_count=5,
                age_seconds=10.0,
                max_age_seconds=300.0,
            ),
            "ERROR",
        )
        self.assertEqual(
            compute_summary_state(
                transport_connected=True,
                backend_error=False,
                observation_count=0,
                age_seconds=None,
                max_age_seconds=300.0,
            ),
            "NO_DATA",
        )
        self.assertEqual(
            compute_summary_state(
                transport_connected=True,
                backend_error=False,
                observation_count=2,
                age_seconds=301.0,
                max_age_seconds=300.0,
            ),
            "STALE",
        )
        self.assertEqual(
            compute_summary_state(
                transport_connected=True,
                backend_error=False,
                observation_count=2,
                age_seconds=30.0,
                max_age_seconds=300.0,
            ),
            "READY",
        )

    def test_disallowed_transition_from_ready_to_no_data_rejected(self) -> None:
        validate_transition("NO_DATA", "READY", self.schema)
        validate_transition("READY", "STALE", self.schema)
        with self.assertRaises(ValueError):
            validate_transition("READY", "NO_DATA", self.schema)


if __name__ == "__main__":
    unittest.main()
