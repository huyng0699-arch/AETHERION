"""Sensor disconnection as technical alert (Q-0169).

A silent or disconnected device creates a technical event distinct from a medical emergency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from apps.server.src.aetherion_server.signal_state import (
    TechnicalSourceState,
    classify_technical_source_state,
)


@dataclass(frozen=True)
class TechnicalAlert:
    alert_id: str
    source_id: str
    subject_id: str
    alert_category: str
    technical_state: str
    medical_emergency: bool
    inferred_unresponsiveness: bool
    requires_device_check: bool
    reason: str
    age_seconds: float | None
    created_at_utc: str


def evaluate_sensor_disconnection(
    *,
    alert_id: str,
    source_id: str,
    subject_id: str,
    link_connected: bool,
    sensor_error: bool,
    last_observed_at: str | None,
    stale_after_seconds: float = 300.0,
    now: datetime | None = None,
) -> TechnicalAlert | None:
    """Emit a technical alert when a sensor is disconnected, errored, silent, or stale."""
    if not alert_id.strip():
        raise ValueError("alert_id must be non-empty")

    ref_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    state: TechnicalSourceState = classify_technical_source_state(
        source_id=source_id,
        subject_id=subject_id,
        link_connected=link_connected,
        sensor_error=sensor_error,
        last_observed_at=last_observed_at,
        stale_after_seconds=stale_after_seconds,
        now=ref_now,
    )

    if state.technical_state == "SIGNAL_PRESENT":
        return None

    return TechnicalAlert(
        alert_id=alert_id.strip(),
        source_id=state.source_id,
        subject_id=state.subject_id,
        alert_category="TECHNICAL_ALERT",
        technical_state=state.technical_state,
        medical_emergency=False,
        inferred_unresponsiveness=False,
        requires_device_check=True,
        reason=state.reason,
        age_seconds=state.age_seconds,
        created_at_utc=ref_now.isoformat(),
    )
