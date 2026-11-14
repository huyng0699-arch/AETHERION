"""Fail-closed privacy boundary for Personal mood and free-text narratives.

This is a UI-side defence in depth, NOT a replacement for server authorization.
The server must issue a verified subject binding and an explicit permission to
read private notes; general CREW observation access is insufficient.
Private text is never translated or copied into a crew-wide summary.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence


@dataclass(frozen=True)
class NarrativeAccess:
    """Build only from a successful trusted server-side identity/consent check."""

    role: str
    verified_subject_id: str | None
    can_read_private_text: bool
    server_authorized: bool


@dataclass(frozen=True)
class NarrativeRecord:
    subject_id: str
    text: str
    observed_at: str
    source_id: str


@dataclass(frozen=True)
class NarrativeProjection:
    status: str
    subject_id: str | None
    records: tuple[NarrativeRecord, ...]


def _time(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("missing observation time")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("invalid observation time") from error
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("unqualified observation time")
    return dt.isoformat()


def private_narrative_projection(
    target_subject_id: str,
    access: NarrativeAccess,
    records: Sequence[Mapping[str, object]] | None,
    *,
    http_status: int | None,
) -> NarrativeProjection:
    """Project text only when *every* privacy and provenance gate succeeds.

    No count/length, subject identity, or partial record is returned for denied
    users. An admin/operator/flight_surgeon observing crew-wide metrics is not
    silently entitled to an individual's mood diary.
    """
    denied = NarrativeProjection("DENIED", None, ())
    if http_status in (401, 403) or http_status is None:
        return denied
    if http_status != 200:
        return NarrativeProjection("OFFLINE" if http_status == 503 else "ERROR", None, ())
    if not isinstance(access, NarrativeAccess):
        return denied
    if (
        access.role != "crew"
        or not access.server_authorized
        or not access.can_read_private_text
        or not isinstance(target_subject_id, str)
        or not target_subject_id.strip()
        or target_subject_id != access.verified_subject_id
    ):
        return denied
    if not isinstance(records, (list, tuple)):
        return NarrativeProjection("ERROR", None, ())
    prepared: list[NarrativeRecord] = []
    try:
        for item in records:
            if not isinstance(item, Mapping) or item.get("subject_id") != target_subject_id:
                raise ValueError("mixed identity or malformed record")
            content = item.get("text")
            origin = item.get("source_id")
            if (
                not isinstance(content, str)
                or not content.strip()
                or not isinstance(origin, str)
                or not origin.strip()
            ):
                raise ValueError("missing private text or source provenance")
            prepared.append(
                NarrativeRecord(
                    target_subject_id,
                    content,  # preserve user's own words, no machine translation
                    _time(item.get("observed_at")),
                    origin.strip(),
                )
            )
    except (TypeError, ValueError):
        return NarrativeProjection("ERROR", None, ())
    return NarrativeProjection("READY" if prepared else "NO_DATA", target_subject_id, tuple(prepared))


def strip_private_fields_for_crew_overview(record: Mapping[str, object]) -> dict[str, object]:
    """Never pass narrative payload/metadata through an overview widget.

    This is a presentation whitelist only; server access checks are mandatory
    for all fields. It deliberately does not preserve arbitrary extra keys,
    note identifiers, sentiment, record counts or free-text-derived features.
    """
    if not isinstance(record, Mapping):
        raise TypeError("crew overview record must be a mapping")
    allowed = ("subject_id", "metric", "value", "unit", "observed_at",
               "source_id", "scope", "quality", "verification_state")
    return {key: record[key] for key in allowed if key in record}
