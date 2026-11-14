"""Q-0065: typed incident display boundary for the native Mission view.

This module never creates an incident from NO_DATA, OFFLINE or absence of a
self-report. No event source is connected until a real server contract exists.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Any


TECHNICAL = "TECHNICAL"
SELF_REPORTED = "SELF_REPORTED"
CLINICAL_REVIEWED = "CLINICAL_REVIEWED"
SUPPORTED_KINDS = frozenset({TECHNICAL, SELF_REPORTED, CLINICAL_REVIEWED})
TECHNICAL_SCOPES = frozenset({"SERVER", "NETWORK", "DEVICE", "CABIN", "VEHICLE", "HABITAT", "SYSTEM"})


@dataclass(frozen=True)
class EventRow:
    event_id: str
    title: str
    kind: str
    scope: str
    source_id: str
    observed_at: str
    subject_id: str = ""


@dataclass(frozen=True)
class EventLists:
    technical: tuple[EventRow, ...]
    health: tuple[EventRow, ...]
    withheld: int = 0


def _timestamp(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("event timestamp missing")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid event timestamp") from exc
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("event timestamp needs timezone")
    return dt.astimezone(timezone.utc).isoformat()


def split_events(records: Iterable[Mapping[str, Any]], allowed_subject_ids: Iterable[str]) -> EventLists:
    """Fail closed on malformed/provenance-free events; filter private subjects.

    The input is an authorized future server event response, never generated
    from a missing sensor. A user self-report is not a clinical diagnosis.
    """
    allowed = frozenset(allowed_subject_ids)
    technical: list[EventRow] = []
    health: list[EventRow] = []
    withheld = 0
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError("event must be an object")
        eid = record.get("event_id")
        kind = record.get("kind")
        title = record.get("title")
        scope = record.get("scope")
        source = record.get("source_id")
        if (not all(isinstance(x, str) and x.strip() for x in (eid, kind, title, scope, source))
                or kind not in SUPPORTED_KINDS):
            raise ValueError("event missing identity, kind or provenance")
        if eid in seen:
            raise ValueError("duplicate event ID")
        seen.add(eid)
        at = _timestamp(record.get("observed_at"))
        sid = record.get("subject_id") or ""
        if not isinstance(sid, str):
            raise ValueError("invalid subject_id")
        if kind == TECHNICAL:
            # Technical events must never carry an individual health profile.
            if sid or scope not in TECHNICAL_SCOPES:
                raise ValueError("technical incident must not expose crew health")
            technical.append(EventRow(eid, title, kind, scope, source, at))
            continue
        if scope != "CREW" or not sid:
            raise ValueError("health event requires a named CREW subject")
        if kind == SELF_REPORTED and record.get("source_kind") != SELF_REPORTED:
            raise ValueError("user report cannot be promoted from an unknown source")
        if kind == CLINICAL_REVIEWED:
            if not isinstance(record.get("reviewer_id"), str) or not record["reviewer_id"].strip():
                raise ValueError("clinical review requires reviewer identity")
            _timestamp(record.get("reviewed_at"))
        if sid not in allowed:
            withheld += 1
            continue
        health.append(EventRow(eid, title, kind, scope, source, at, sid))
    technical.sort(key=lambda e: e.observed_at, reverse=True)
    health.sort(key=lambda e: e.observed_at, reverse=True)
    return EventLists(tuple(technical), tuple(health), withheld)


def build_mission_events_widget(parent=None):
    """Native Qt event list; callers must supply real authorized server events."""
    from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

    class MissionEventList(QWidget):
        def __init__(self):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            self.note = QLabel("NO_DATA — no event service connected; no health incident inferred")
            self.note.setWordWrap(True)
            layout.addWidget(self.note)
            layout.addWidget(QLabel("Technical / environmental incidents (not medical diagnoses)"))
            self.technical = QTableWidget(0, 4)
            self.technical.setHorizontalHeaderLabels(["Event", "Observed at", "Source", "Scope"])
            self.technical.setAccessibleName("Technical incidents")
            layout.addWidget(self.technical)
            layout.addWidget(QLabel("User reports / reviewed health events (authorized subjects only)"))
            self.health = QTableWidget(0, 4)
            self.health.setHorizontalHeaderLabels(["Event", "Type", "Observed at", "Source"])
            self.health.setAccessibleName("Authorized health events")
            layout.addWidget(self.health)
            for table in (self.technical, self.health):
                table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        def set_events(self, records, allowed_subject_ids):
            result = split_events(records, allowed_subject_ids)
            self.technical.setRowCount(len(result.technical))
            for i, event in enumerate(result.technical):
                for j, field in enumerate((event.title, event.observed_at, event.source_id, event.scope)):
                    self.technical.setItem(i, j, QTableWidgetItem(field))
            self.health.setRowCount(len(result.health))
            for i, event in enumerate(result.health):
                for j, field in enumerate((event.title, event.kind, event.observed_at, event.source_id)):
                    self.health.setItem(i, j, QTableWidgetItem(field))
            self.note.setText(
                f"Loaded: {len(result.technical)} technical / {len(result.health)} authorized health events; "
                "Restricted subjects are never displayed. No automatic diagnoses."
            )

    return MissionEventList()
