"""Source-backed native Qt panels that never conflate cabin and crew readings.

Q-0066 standalone adapter. The parent authenticates and requests each scope
separately from the actual local server; this component does not cache tokens,
invent measurements, or modify the existing Mission Control shell.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit

from .crew_data_state import CrewMeasurement, state_from_server_response

SCOPE_NAMES = {
    "CREW": frozenset({"CREW", "crew", "personal"}),
    "CABIN": frozenset({"CABIN", "habitat"}),
}
SCOPE_LABELS = {
    "CREW": "Crew · individual observations",
    "CABIN": "Cabin · shared environment (not personal health)",
}


@dataclass(frozen=True)
class ScopePanelState:
    subject_id: str
    scope: str
    status: str
    label: str
    note: str
    rows: tuple[CrewMeasurement, ...]


def observations_url(api_url: str, subject_id: str, scope: str) -> str:
    """Construct a separately scoped server query; never allow query injection."""
    if scope not in SCOPE_NAMES:
        raise ValueError("scope must be CREW or CABIN")
    if not isinstance(subject_id, str) or not 1 <= len(subject_id.strip()) <= 80:
        raise ValueError("a subject ID is required")
    if any(ord(ch) < 32 for ch in subject_id):
        raise ValueError("control characters are not valid in subject IDs")
    if not isinstance(api_url, str):
        raise ValueError("API URL must be a string")
    url = urlsplit(api_url)
    if (url.scheme not in {"http", "https"} or not url.hostname or url.username or
            url.password or url.query or url.fragment or url.path not in {"", "/"}):
        raise ValueError("provide a configured HTTP(S) server base URL without credentials")
    return api_url.rstrip("/") + "/api/v1/observations?" + urlencode({
        "subject_id": subject_id.strip(), "scope": scope, "limit": 100,
    })


def panel_from_response(subject_id: str, scope: str, status_code: int | None,
                        payload: object = None, *, now=None, network_error: bool = False) -> ScopePanelState:
    """Fail closed if a record crosses crew/cabin scope or subject boundaries."""
    if scope not in SCOPE_NAMES:
        raise ValueError("scope must be CREW or CABIN")
    snapshot = state_from_server_response(subject_id, status_code, payload, now=now,
                                          network_error=network_error)
    if any(row.scope not in SCOPE_NAMES[scope] for row in snapshot.measurements):
        return ScopePanelState(subject_id, scope, "ERROR", SCOPE_LABELS[scope],
                               "Scope mismatch — no observations can be displayed", ())
    note = snapshot.message
    if scope == "CABIN":
        note += " · Environmental scope; never an individual diagnosis"
    return ScopePanelState(subject_id, scope, snapshot.status, SCOPE_LABELS[scope],
                           note, snapshot.measurements)


def build_scope_panels(crew: ScopePanelState, cabin: ScopePanelState, parent=None):
    """Native content panels with explicit labels and no invented readings."""
    from PySide6.QtWidgets import (QGroupBox, QHeaderView, QLabel, QTableWidget,
                                   QTableWidgetItem, QVBoxLayout, QWidget)

    if crew.scope != "CREW" or cabin.scope != "CABIN":
        raise ValueError("expected explicitly separated CREW and CABIN panels")
    root = QWidget(parent)
    layout = QVBoxLayout(root)
    for state in (crew, cabin):
        group = QGroupBox(state.label)
        group.setAccessibleName(state.label)
        group_layout = QVBoxLayout(group)
        status_label = QLabel(f"{state.status} — {state.note}")
        status_label.setWordWrap(True)
        group_layout.addWidget(status_label)
        table = QTableWidget(len(state.rows), 6)
        table.setHorizontalHeaderLabels(["Metric", "Recorded value", "Observed at",
                                         "Source", "Scope", "Quality"])
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAccessibleName(f"{state.scope} source-backed observations")
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        for row_index, record in enumerate(state.rows):
            values = (record.metric, f"{record.value:g} {record.unit}", record.observed_at,
                      record.source_id, record.scope, record.quality)
            for column, value in enumerate(values):
                table.setItem(row_index, column, QTableWidgetItem(value))
        group_layout.addWidget(table)
        layout.addWidget(group)
    return root
