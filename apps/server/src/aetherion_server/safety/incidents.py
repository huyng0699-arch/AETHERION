"""Crew assistance incident routing with exact identity (Q-0170) and ACK semantics (Q-0171)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class RoutedAssistanceEvent:
    event_id: str
    incident_id: str
    subject_id: str
    actor_id: str
    event_kind: str
    source: str
    recorded_at_utc: str
    note: str = ""


@dataclass
class SafetyIncident:
    incident_id: str
    subject_id: str
    mission_id: str
    incident_type: str
    source: str
    created_at_utc: str
    status: str = "OPEN"
    acknowledged_by: str | None = None
    acknowledged_at_utc: str | None = None
    events: list[RoutedAssistanceEvent] = field(default_factory=list)


class IncidentRegistry:
    """Authoritative incident registry enforcing exact crew+incident routing and non-duplicating ACK."""

    def __init__(self) -> None:
        self._incidents: dict[str, SafetyIncident] = {}

    def create_incident(
        self,
        *,
        incident_id: str,
        subject_id: str,
        mission_id: str,
        incident_type: str,
        source: str,
        now: datetime | None = None,
    ) -> SafetyIncident:
        if not incident_id.strip():
            raise ValueError("incident_id must be non-empty")
        if not subject_id.strip():
            raise ValueError("subject_id must be non-empty")
        if not mission_id.strip():
            raise ValueError("mission_id must be non-empty")
        if not incident_type.strip():
            raise ValueError("incident_type must be non-empty")
        if not source.strip():
            raise ValueError("source must be non-empty")
        if incident_id in self._incidents:
            raise ValueError(f"Duplicate incident_id: {incident_id}")

        ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        inc = SafetyIncident(
            incident_id=incident_id.strip(),
            subject_id=subject_id.strip(),
            mission_id=mission_id.strip(),
            incident_type=incident_type.strip(),
            source=source.strip(),
            created_at_utc=ts,
        )
        self._incidents[inc.incident_id] = inc
        return inc

    def route_assistance_event(
        self,
        *,
        event_id: str,
        incident_id: str,
        subject_id: str,
        actor_id: str,
        event_kind: str,
        source: str,
        note: str = "",
        now: datetime | None = None,
    ) -> RoutedAssistanceEvent:
        """Route an assistance event strictly to an existing incident with matching subject_id."""
        if incident_id not in self._incidents:
            raise KeyError(f"Unknown incident_id: {incident_id}")
        inc = self._incidents[incident_id]
        if subject_id.strip() != inc.subject_id:
            raise ValueError(
                f"Identity mismatch for incident {incident_id}: expected subject_id={inc.subject_id!r}, got {subject_id!r}"
            )
        if not event_id.strip() or not actor_id.strip() or not event_kind.strip() or not source.strip():
            raise ValueError("event_id, actor_id, event_kind, and source must be non-empty")

        ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        ev = RoutedAssistanceEvent(
            event_id=event_id.strip(),
            incident_id=inc.incident_id,
            subject_id=inc.subject_id,
            actor_id=actor_id.strip(),
            event_kind=event_kind.strip(),
            source=source.strip(),
            recorded_at_utc=ts,
            note=note.strip(),
        )
        inc.events.append(ev)
        return ev

    def acknowledge_incident(
        self,
        *,
        incident_id: str,
        acknowledged_by: str,
        event_id: str,
        source: str = "crew_ack",
        note: str = "",
        now: datetime | None = None,
    ) -> SafetyIncident:
        """Update existing incident to ACKNOWLEDGED without creating a new medical event."""
        if incident_id not in self._incidents:
            raise KeyError(f"Unknown incident_id: {incident_id}")
        if not acknowledged_by.strip():
            raise ValueError("acknowledged_by must be non-empty")

        inc = self._incidents[incident_id]
        ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
        inc.status = "ACKNOWLEDGED"
        inc.acknowledged_by = acknowledged_by.strip()
        inc.acknowledged_at_utc = ts
        self.route_assistance_event(
            event_id=event_id,
            incident_id=inc.incident_id,
            subject_id=inc.subject_id,
            actor_id=acknowledged_by.strip(),
            event_kind="ALERT_ACKNOWLEDGED",
            source=source,
            note=note,
            now=now,
        )
        return inc

    def list_incidents(self, subject_id: str | None = None) -> list[SafetyIncident]:
        items = list(self._incidents.values())
        if subject_id is not None:
            items = [i for i in items if i.subject_id == subject_id]
        return items
