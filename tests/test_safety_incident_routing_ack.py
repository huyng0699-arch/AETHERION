"""Deterministic tests for Q-0170 (crew event routing with identity) and Q-0171 (ACK semantics)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_SRC = REPO_ROOT / "apps" / "server" / "src"
for p in (str(REPO_ROOT), str(SERVER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from apps.server.src.aetherion_server.safety.incidents import IncidentRegistry  # noqa: E402


class SafetyIncidentRoutingAndAckTests(unittest.TestCase):
    def test_event_routing_enforces_exact_crew_and_incident_identity(self) -> None:
        reg = IncidentRegistry()
        now = datetime(2026, 11, 14, 9, 22, tzinfo=timezone.utc)
        reg.create_incident(
            incident_id="inc-001",
            subject_id="crew-alpha",
            mission_id="artemis-sim-1",
            incident_type="NEED_HELP_NOW",
            source="desktop_button",
            now=now,
        )
        ev = reg.route_assistance_event(
            event_id="ev-001",
            incident_id="inc-001",
            subject_id="crew-alpha",
            actor_id="crew-bravo",
            event_kind="WITNESS_CHECK",
            source="crew_console",
            note="Visual check initiated",
            now=now,
        )
        self.assertEqual(ev.incident_id, "inc-001")
        self.assertEqual(ev.subject_id, "crew-alpha")

        with self.assertRaises(ValueError):
            reg.route_assistance_event(
                event_id="ev-002",
                incident_id="inc-001",
                subject_id="crew-other",
                actor_id="crew-bravo",
                event_kind="WITNESS_CHECK",
                source="crew_console",
                now=now,
            )

    def test_ack_updates_existing_incident_without_generating_new_medical_event(self) -> None:
        reg = IncidentRegistry()
        now = datetime(2026, 11, 14, 9, 22, tzinfo=timezone.utc)
        reg.create_incident(
            incident_id="inc-002",
            subject_id="crew-alpha",
            mission_id="artemis-sim-1",
            incident_type="NEED_HELP_NOW",
            source="desktop_button",
            now=now,
        )
        updated = reg.acknowledge_incident(
            incident_id="inc-002",
            acknowledged_by="cmo-01",
            event_id="ev-ack-1",
            note="CMO responding",
            now=now,
        )
        self.assertEqual(updated.status, "ACKNOWLEDGED")
        self.assertEqual(updated.acknowledged_by, "cmo-01")
        self.assertEqual(len(reg.list_incidents()), 1)
        self.assertEqual(updated.events[-1].event_kind, "ALERT_ACKNOWLEDGED")
        self.assertEqual(updated.events[-1].subject_id, "crew-alpha")

        with self.assertRaises(KeyError):
            reg.acknowledge_incident(
                incident_id="inc-missing",
                acknowledged_by="cmo-01",
                event_id="ev-ack-2",
                now=now,
            )


if __name__ == "__main__":
    unittest.main()
