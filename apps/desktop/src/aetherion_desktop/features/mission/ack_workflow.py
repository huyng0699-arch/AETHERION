"""Fail-closed Mission Incident ACK workflow (Q-0068).

An ACK click transitions an existing authorized incident from UNACKNOWLEDGED to
ACKNOWLEDGED only after verified server confirmation, and never creates a new
incident.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence


UNACKNOWLEDGED = "UNACKNOWLEDGED"
ACKNOWLEDGED = "ACKNOWLEDGED"


@dataclass(frozen=True)
class IncidentAckState:
    event_id: str
    ack_state: str = UNACKNOWLEDGED
    acknowledged_by: str | None = None
    acknowledged_at_utc: str | None = None
    note: str = ""


@dataclass(frozen=True)
class AckResult:
    status: str  # "ACKNOWLEDGED" | "NOT_FOUND" | "DENIED" | "OFFLINE" | "ERROR"
    events: tuple[IncidentAckState, ...]
    updated_event: IncidentAckState | None
    incident_created: bool = False
    label_vi: str = ""
    label_en: str = ""


def _parse_utc(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None or dt.utcoffset() is None:
        return None
    return dt.astimezone(timezone.utc).isoformat()


def apply_incident_ack(
    events: Sequence[IncidentAckState],
    event_id: str,
    operator_id: str,
    access_token: str,
    http_status: int | None,
    payload: object,
    note: str = "",
) -> AckResult:
    """Verify server ACK response for an existing event without creating any incident."""
    base_events = tuple(events)
    if not isinstance(operator_id, str) or not operator_id.strip() or not isinstance(access_token, str) or not access_token.strip():
        return AckResult(
            status="DENIED",
            events=base_events,
            updated_event=None,
            incident_created=False,
            label_vi="Chưa xác thực người vận hành hoặc phiên làm việc",
            label_en="Operator identity or session token required",
        )

    target_id = str(event_id or "").strip()
    if not target_id or all(ev.event_id != target_id for ev in base_events):
        return AckResult(
            status="NOT_FOUND",
            events=base_events,
            updated_event=None,
            incident_created=False,
            label_vi="Không tìm thấy sự kiện để xác nhận (không tạo sự cố mới)",
            label_en="Incident not found for ACK (no new incident created)",
        )

    if http_status is None:
        return AckResult(
            status="OFFLINE",
            events=base_events,
            updated_event=None,
            incident_created=False,
            label_vi="Mất kết nối máy chủ — chưa ghi nhận ACK",
            label_en="Server offline — ACK not recorded",
        )

    if http_status != 200 or not isinstance(payload, Mapping):
        return AckResult(
            status="ERROR",
            events=base_events,
            updated_event=None,
            incident_created=False,
            label_vi="Máy chủ từ chối xác nhận ACK",
            label_en="Server rejected ACK request",
        )

    ack_at = _parse_utc(payload.get("acknowledged_at"))
    if (
        payload.get("event_id") != target_id
        or payload.get("ack_state") != ACKNOWLEDGED
        or payload.get("acknowledged_by") != operator_id.strip()
        or ack_at is None
    ):
        return AckResult(
            status="ERROR",
            events=base_events,
            updated_event=None,
            incident_created=False,
            label_vi="Phản hồi ACK từ máy chủ không hợp lệ",
            label_en="Invalid server ACK payload",
        )

    updated_list: list[IncidentAckState] = []
    updated_item: IncidentAckState | None = None
    for ev in base_events:
        if ev.event_id == target_id:
            updated_item = IncidentAckState(
                event_id=ev.event_id,
                ack_state=ACKNOWLEDGED,
                acknowledged_by=operator_id.strip(),
                acknowledged_at_utc=ack_at,
                note=str(note or "").strip(),
            )
            updated_list.append(updated_item)
        else:
            updated_list.append(ev)

    return AckResult(
        status="ACKNOWLEDGED",
        events=tuple(updated_list),
        updated_event=updated_item,
        incident_created=False,
        label_vi="Đã xác nhận sự cố (ACK)",
        label_en="Incident acknowledged (ACK)",
    )
