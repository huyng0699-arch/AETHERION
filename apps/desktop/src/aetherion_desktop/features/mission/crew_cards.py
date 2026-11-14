"""Native Mission Control crew card, driven only by authenticated API state.

This is a reusable widget, not a fake crew roster. The containing Qt screen must
supply an authorized subject selection and an actual server response snapshot.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable


DISPLAY_STATES = frozenset({"READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"})


@dataclass(frozen=True)
class CrewCardModel:
    subject_id: str
    status: str
    last_observed_at: str | None
    latest_source_id: str | None
    measurement_count: int
    display_note: str
    allow_open: bool


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be a string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return dt


def card_from_state(subject_id: str, state: object) -> CrewCardModel:
    """Reject mismatched/uncertain identity; never synthesize vitals or a crew list."""
    if not isinstance(subject_id, str) or not subject_id.strip() or len(subject_id) > 80:
        raise ValueError("explicit subject ID is required")
    if getattr(state, "subject_id", None) != subject_id:
        raise ValueError("subject identity mismatch")
    status = getattr(state, "status", None)
    if status not in DISPLAY_STATES:
        raise ValueError("unknown server state")
    rows = getattr(state, "measurements", None)
    if not isinstance(rows, tuple):
        raise ValueError("server state lacks validated measurement tuple")
    if status in {"DENIED", "OFFLINE", "ERROR"} and rows:
        raise ValueError("restricted/error state cannot expose cached observations")
    if not rows:
        return CrewCardModel(subject_id, status, None, None, 0,
                             f"{status} — no current observation shown", status not in {"DENIED", "ERROR"})

    sorted_rows = []
    for obs in rows:
        if getattr(obs, "subject_id", None) != subject_id:
            raise ValueError("mixed-subject observations")
        source = getattr(obs, "source_id", None)
        if not isinstance(source, str) or not source.strip():
            raise ValueError("source provenance is missing")
        observed = getattr(obs, "observed_at", None)
        sorted_rows.append((_timestamp(observed), observed, source))
    sorted_rows.sort(key=lambda value: value[0], reverse=True)
    _, observed_at, source_id = sorted_rows[0]
    return CrewCardModel(subject_id, status, observed_at, source_id, len(rows),
                         "Latest recorded observation, not a medical verdict", True)


def build_crew_card(model: CrewCardModel, on_open: Callable[[str], None], parent=None):
    """Build a native Qt card; opening returns the *same* selected subject ID.

    PySide6 is imported only during native UI use. This code deliberately does
    not fetch a server or save health data itself.
    """
    from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

    card = QFrame(parent)
    card.setObjectName("crewProfileCard")
    card.setAccessibleName(f"Crew profile {model.subject_id}")
    layout = QVBoxLayout(card)
    title = QLabel(model.subject_id)
    title.setAccessibleName("Exact authorized subject ID")
    layout.addWidget(title)
    layout.addWidget(QLabel(f"Source status: {model.status}"))
    if model.last_observed_at and model.latest_source_id:
        layout.addWidget(QLabel(f"Last observation: {model.last_observed_at}"))
        layout.addWidget(QLabel(f"Recorded source: {model.latest_source_id}"))
        layout.addWidget(QLabel(f"Recorded points: {model.measurement_count}"))
    else:
        layout.addWidget(QLabel("No source-backed observation available"))
    layout.addWidget(QLabel(model.display_note))
    button = QPushButton("Open exact profile")
    button.setEnabled(model.allow_open)
    button.setAccessibleName(f"Open profile {model.subject_id}")
    button.clicked.connect(lambda checked=False: on_open(model.subject_id))
    layout.addWidget(button)
    return card
