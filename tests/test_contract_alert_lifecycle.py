"""Contract tests for Q-0024 alert lifecycle events."""

from datetime import datetime
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "packages" / "contracts" / "alert_lifecycle.schema.json"


def validate_alert_event(event: dict, schema: dict) -> None:
    required = set(schema["required"])
    missing = required - set(event.keys())
    if missing:
        raise ValueError(f"missing required fields: {sorted(missing)}")
    extra = set(event.keys()) - set(schema["properties"].keys())
    if extra:
        raise ValueError(f"unexpected fields: {sorted(extra)}")
    if event["scope"] not in schema["properties"]["scope"]["enum"]:
        raise ValueError(f"invalid scope: {event['scope']}")
    if event["severity"] not in schema["properties"]["severity"]["enum"]:
        raise ValueError(f"invalid severity: {event['severity']}")

    event_type = event["event_type"]
    transitions = schema["x-lifecycle-transitions"]
    if event_type not in transitions:
        raise ValueError(f"unknown event_type: {event_type}")
    rule = transitions[event_type]
    if event["previous_state"] not in rule["from"]:
        raise ValueError(
            f"invalid transition for {event_type}: from {event['previous_state']!r}"
        )
    if event["next_state"] != rule["to"]:
        raise ValueError(
            f"invalid next_state for {event_type}: expected {rule['to']!r}, got {event['next_state']!r}"
        )
    if not str(event["actor_id"]).strip():
        raise ValueError("actor_id must be non-empty")
    if not str(event["reason"]).strip():
        raise ValueError("reason must be non-empty")
    if not event["source_observation_ids"]:
        raise ValueError("source_observation_ids must be non-empty")

    dt = datetime.fromisoformat(event["occurred_at"])
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("occurred_at must include timezone offset")


class AlertLifecycleContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_differentiates_all_four_lifecycle_events(self) -> None:
        expected = [
            "incident_created",
            "incident_acknowledged",
            "incident_escalated",
            "incident_resolved",
        ]
        self.assertEqual(self.schema["properties"]["event_type"]["enum"], expected)
        self.assertEqual(list(self.schema["x-lifecycle-transitions"].keys()), expected)

    def test_valid_alert_lifecycle_sequence_passes(self) -> None:
        sequence = [
            {
                "event_id": "evt-001",
                "incident_id": "inc-crew1-001",
                "subject_id": "CREW-1",
                "scope": "CREW",
                "event_type": "incident_created",
                "previous_state": None,
                "next_state": "created",
                "severity": "WARNING",
                "actor_id": "rule_engine:vitals_threshold",
                "occurred_at": "2026-11-14T05:00:00+00:00",
                "reason": "Heart rate exceeded configured threshold",
                "source_observation_ids": [101],
            },
            {
                "event_id": "evt-002",
                "incident_id": "inc-crew1-001",
                "subject_id": "CREW-1",
                "scope": "CREW",
                "event_type": "incident_acknowledged",
                "previous_state": "created",
                "next_state": "acknowledged",
                "severity": "WARNING",
                "actor_id": "flight_surgeon:dr_lin",
                "occurred_at": "2026-11-14T05:02:00+00:00",
                "reason": "Crew alerted; initiating recheck protocol",
                "source_observation_ids": [101],
            },
            {
                "event_id": "evt-003",
                "incident_id": "inc-crew1-001",
                "subject_id": "CREW-1",
                "scope": "CREW",
                "event_type": "incident_escalated",
                "previous_state": "acknowledged",
                "next_state": "escalated",
                "severity": "CRITICAL",
                "actor_id": "flight_surgeon:dr_lin",
                "occurred_at": "2026-11-14T05:05:00+00:00",
                "reason": "Sustained tachycardia on recheck",
                "source_observation_ids": [101, 102],
            },
            {
                "event_id": "evt-004",
                "incident_id": "inc-crew1-001",
                "subject_id": "CREW-1",
                "scope": "CREW",
                "event_type": "incident_resolved",
                "previous_state": "escalated",
                "next_state": "resolved",
                "severity": "INFO",
                "actor_id": "flight_surgeon:dr_lin",
                "occurred_at": "2026-11-14T05:20:00+00:00",
                "reason": "Vitals returned to baseline after rest",
                "source_observation_ids": [101, 102, 103],
            },
        ]
        for event in sequence:
            validate_alert_event(event, self.schema)

    def test_invalid_transitions_and_missing_provenance_rejected(self) -> None:
        bad_resolved_to_ack = {
            "event_id": "evt-bad-1",
            "incident_id": "inc-crew1-001",
            "subject_id": "CREW-1",
            "scope": "CREW",
            "event_type": "incident_acknowledged",
            "previous_state": "resolved",
            "next_state": "acknowledged",
            "severity": "WARNING",
            "actor_id": "flight_surgeon:dr_lin",
            "occurred_at": "2026-11-14T05:25:00+00:00",
            "reason": "Invalid transition from resolved",
            "source_observation_ids": [103],
        }
        with self.assertRaises(ValueError):
            validate_alert_event(bad_resolved_to_ack, self.schema)

        bad_naive_time = dict(bad_resolved_to_ack)
        bad_naive_time["previous_state"] = "created"
        bad_naive_time["occurred_at"] = "2026-11-14T05:25:00"
        with self.assertRaises(ValueError):
            validate_alert_event(bad_naive_time, self.schema)


if __name__ == "__main__":
    unittest.main()
