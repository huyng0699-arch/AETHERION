"""Assistance follow-up care episode linkage (Q-0172).

From an acknowledged safety alert/incident, opens a linked CareEpisode in
CareEpisodeStore and preserves the full incident event history.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

from apps.server.src.aetherion_server.care.episode import CareEpisodeStore
from apps.server.src.aetherion_server.safety.incidents import (
    RoutedAssistanceEvent,
    SafetyIncident,
)


@dataclass(frozen=True)
class FollowupCareLink:
    incident_id: str
    subject_id: str
    episode_id: str
    opened_by: str
    opened_at_utc: str
    preserved_event_count: int
    episode: dict[str, Any]


def open_followup_care_episode(
    incident: SafetyIncident,
    care_store: CareEpisodeStore,
    *,
    actor_id: str,
    chief_concern: str | None = None,
    event_id: str = "ev-care-followup",
    now: datetime | None = None,
) -> FollowupCareLink:
    """Open a linked CareEpisode from an acknowledged SafetyIncident, preserving event history."""
    if incident.status != "ACKNOWLEDGED":
        raise ValueError(
            f"Incident {incident.incident_id} must be ACKNOWLEDGED before opening follow-up care (got {incident.status!r})"
        )
    if not actor_id.strip():
        raise ValueError("actor_id must be non-empty")

    ts = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    preserved_history = [asdict(ev) for ev in incident.events]
    concern = (chief_concern or f"Follow-up for {incident.incident_type}").strip()

    episode = care_store.start_episode(
        subject_id=incident.subject_id,
        actor_id=actor_id.strip(),
        chief_concern=concern,
        source=f"safety_incident:{incident.incident_id}",
        unit="episode",
        data_state="READY",
        recorded_at=ts,
        payload={
            "incident_id": incident.incident_id,
            "mission_id": incident.mission_id,
            "incident_type": incident.incident_type,
            "acknowledged_by": incident.acknowledged_by,
            "acknowledged_at_utc": incident.acknowledged_at_utc,
            "incident_event_history": preserved_history,
        },
        ai_assisted=False,
        human_confirmed=True,
    )

    incident.events.append(
        RoutedAssistanceEvent(
            event_id=event_id.strip() or "ev-care-followup",
            incident_id=incident.incident_id,
            subject_id=incident.subject_id,
            actor_id=actor_id.strip(),
            event_kind="CARE_FOLLOWUP_OPENED",
            source=f"care_episode:{episode['episode_id']}",
            recorded_at_utc=ts,
            note=f"Opened linked care episode {episode['episode_id']}",
        )
    )

    return FollowupCareLink(
        incident_id=incident.incident_id,
        subject_id=incident.subject_id,
        episode_id=episode["episode_id"],
        opened_by=actor_id.strip(),
        opened_at_utc=ts,
        preserved_event_count=len(preserved_history),
        episode=episode,
    )
