"""Technical source signal state classification without clinical inference (Q-0036)."""

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class TechnicalSourceState:
    source_id: str
    subject_id: str
    technical_state: str
    inferred_unresponsiveness: bool
    clinical_incident_inferred: bool
    reason: str
    age_seconds: float | None


def classify_technical_source_state(
    *,
    source_id: str,
    subject_id: str,
    link_connected: bool,
    sensor_error: bool,
    last_observed_at: str | None,
    stale_after_seconds: float = 300.0,
    now: datetime | None = None,
) -> TechnicalSourceState:
    """Classify technical telemetry availability without inferring crew unresponsiveness."""
    if not source_id.strip():
        raise ValueError("source_id must be non-empty")
    if not subject_id.strip():
        raise ValueError("subject_id must be non-empty")
    if stale_after_seconds <= 0:
        raise ValueError("stale_after_seconds must be positive")

    if not link_connected:
        return TechnicalSourceState(
            source_id=source_id,
            subject_id=subject_id,
            technical_state="SENSOR_OFFLINE",
            inferred_unresponsiveness=False,
            clinical_incident_inferred=False,
            reason="Telemetry link disconnected; technical outage only.",
            age_seconds=None,
        )
    if sensor_error:
        return TechnicalSourceState(
            source_id=source_id,
            subject_id=subject_id,
            technical_state="LINK_ERROR",
            inferred_unresponsiveness=False,
            clinical_incident_inferred=False,
            reason="Sensor/link fault reported; no clinical incident inferred.",
            age_seconds=None,
        )
    if last_observed_at is None:
        return TechnicalSourceState(
            source_id=source_id,
            subject_id=subject_id,
            technical_state="NO_SIGNAL",
            inferred_unresponsiveness=False,
            clinical_incident_inferred=False,
            reason="No observations recorded from source; missing data is not unresponsiveness.",
            age_seconds=None,
        )

    observed_dt = datetime.fromisoformat(last_observed_at)
    if observed_dt.tzinfo is None or observed_dt.utcoffset() is None:
        raise ValueError("last_observed_at must be timezone-aware")

    ref_now = now or datetime.now(timezone.utc)
    age = max(0.0, (ref_now - observed_dt.astimezone(timezone.utc)).total_seconds())
    if age > stale_after_seconds:
        return TechnicalSourceState(
            source_id=source_id,
            subject_id=subject_id,
            technical_state="STALE_SIGNAL",
            inferred_unresponsiveness=False,
            clinical_incident_inferred=False,
            reason="Latest signal exceeded freshness threshold; technical staleness only.",
            age_seconds=age,
        )

    return TechnicalSourceState(
        source_id=source_id,
        subject_id=subject_id,
        technical_state="SIGNAL_PRESENT",
        inferred_unresponsiveness=False,
        clinical_incident_inferred=False,
        reason="Fresh technical signal received.",
        age_seconds=age,
    )
