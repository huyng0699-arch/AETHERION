"""Fail-closed, source-identified Personal -> Care episode handoff (Q-0083).

Uses only authenticated observation and Care API payloads supplied by the real
Qt network client. The existing Care API does not persist a foreign key to an
observation, so selecting an observation cannot silently link it to a Care
episode. A user must explicitly choose an existing episode or consent to
creating a new human-reported episode; clinical assessment is never inferred.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Mapping


@dataclass(frozen=True)
class SelectedObservation:
    subject_id: str
    observation_id: int
    metric: str
    source_id: str
    observed_at_utc: str
    quality: str
    verification_state: str


@dataclass(frozen=True)
class CareHandoff:
    status: str
    subject_id: str | None
    selected_observation: SelectedObservation | None
    episode_id: str | None
    create_body: dict | None
    observation_link_persisted: bool = False


def _utc(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("Observation timestamp missing")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError("Observation timezone missing")
    return stamp.astimezone(timezone.utc)


def selected_observation_from_api(
    subject_id: str,
    card: object,
    http_status: int | None,
    payload: object,
) -> SelectedObservation | None:
    """Require ONE exact source-backed API observation for this selected card.

    Card fields are display data only. Authorization must already have been
    performed by the canonical server for this same subject/session.
    """
    if http_status != 200 or not isinstance(payload, Mapping):
        return None
    if not isinstance(subject_id, str) or not subject_id.strip():
        return None
    if payload.get("subject_id") != subject_id:
        return None
    observations = payload.get("observations")
    if not isinstance(observations, list):
        return None
    fields = ("metric", "source_id", "unit", "scope", "quality", "verification_state", "observed_at", "reading")
    if any(not isinstance(getattr(card, field, None), str) or not getattr(card, field).strip() for field in fields):
        return None
    try:
        card_time = _utc(card.observed_at)
    except (ValueError, TypeError):
        return None
    candidates: list[SelectedObservation] = []
    for item in observations:
        if not isinstance(item, Mapping) or item.get("subject_id") != subject_id:
            return None  # mixed/invalid response must not match a stray row
        record_id = item.get("id")
        number = item.get("value")
        if isinstance(record_id, bool) or not isinstance(record_id, int) or record_id <= 0:
            return None
        if isinstance(number, bool) or not isinstance(number, (int, float)) or not isfinite(number):
            return None
        try:
            observed = _utc(item.get("observed_at"))
        except (ValueError, TypeError):
            return None
        unit = item.get("unit")
        source = item.get("source_id")
        verification = item.get("verification_state")
        quality = item.get("quality")
        scope = item.get("scope")
        if (not all(isinstance(v, str) and v.strip() for v in (
                unit, source, quality, verification, scope)) or
                source.lower().startswith(("research:", "nasa_osdr:")) or
                verification == "TEST_FIXTURE" or scope == "engineering_test"):
            return None
        # Personal Today intentionally downgrades raw READY records to
        # UNVERIFIED when the source itself is not verified, or to STALE when
        # the last accepted reading is old. Comparing raw==display quality
        # wrongly rejects those exact, authenticated observations.
        # Never upgrade an unverified source or allow ERROR/DENIED/NO_DATA
        # availability rows to become a Care handoff.
        raw_quality = quality.upper()
        display_quality = card.quality.upper()
        if raw_quality not in {"READY", "STALE", "UNVERIFIED"}:
            return None
        compatible = raw_quality == display_quality or (
            raw_quality == "READY" and (
                display_quality == "UNVERIFIED" or (
                    display_quality == "STALE" and verification == "VERIFIED"
                )
            )
        )
        if observed > datetime.now(timezone.utc):
            return None  # a future-dated row must not initiate a Care episode
        if (item.get("metric") == card.metric and source == card.source_id and
                unit == card.unit and scope == card.scope and
                compatible and verification == card.verification_state and
                observed == card_time and f"{number:g} {unit}" == card.reading):
            candidates.append(SelectedObservation(subject_id, record_id,
                                                    item["metric"], source,
                                                    observed.isoformat(),
                                                    display_quality, verification))
    return candidates[0] if len(candidates) == 1 else None


def resume_explicit_episode(
    selected: SelectedObservation | None,
    http_status: int | None,
    payload: object,
    chosen_episode_id: str | None,
) -> CareHandoff:
    """Never choose the first episode or infer linkage from shared subject."""
    denied = CareHandoff("DENIED", None, None, None, None)
    if selected is None or http_status in (401, 403, None):
        return denied
    if http_status != 200 or not isinstance(payload, Mapping):
        return CareHandoff("ERROR", None, None, None, None)
    if payload.get("subject_id") != selected.subject_id or not isinstance(payload.get("episodes"), list):
        return CareHandoff("ERROR", None, None, None, None)
    episodes = payload["episodes"]
    if not all(isinstance(ep, Mapping) and ep.get("subject_id") == selected.subject_id
               and isinstance(ep.get("episode_id"), str) and ep.get("episode_id")
               for ep in episodes):
        return CareHandoff("ERROR", None, None, None, None)
    if not chosen_episode_id:
        return CareHandoff("SELECT_EPISODE", selected.subject_id, selected, None, None)
    matched = [ep for ep in episodes if ep["episode_id"] == chosen_episode_id]
    if len(matched) != 1:
        return CareHandoff("DENIED", None, None, None, None)
    if matched[0].get("current_phase") == "CLOSED":
        return CareHandoff("CLOSED", selected.subject_id, selected, None, None)
    return CareHandoff("RESUME", selected.subject_id, selected, chosen_episode_id, None)


def prepare_consented_new_episode(
    selected: SelectedObservation | None,
    chief_concern: str,
    *,
    explicit_consent: bool,
) -> CareHandoff:
    """Prepare the current canonical POST /care/episodes body, never send it.

    The user must write their own concern and consent explicitly. Current
    backend creates a source=explicit_user_report UNVERIFIED episode, not a
    record-linked clinical diagnosis. No POST occurs without a user action.
    """
    if selected is None:
        return CareHandoff("DENIED", None, None, None, None)
    if explicit_consent is not True or not isinstance(chief_concern, str):
        return CareHandoff("CONSENT_REQUIRED", selected.subject_id, selected, None, None)
    concern = chief_concern.strip()
    if not 1 <= len(concern) <= 500:
        return CareHandoff("CONCERN_REQUIRED", selected.subject_id, selected, None, None)
    return CareHandoff(
        "CREATE_READY_UNLINKED",
        selected.subject_id,
        selected,
        None,
        {
            "subject_id": selected.subject_id,
            "chief_concern": concern,
            "symptom_terms": [],
            "interview_answers": {},
            "explicit_consent": True,
        },
        False,
    )
