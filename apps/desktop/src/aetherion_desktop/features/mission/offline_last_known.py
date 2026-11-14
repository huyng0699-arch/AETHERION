"""Session-bound last-known readings for Mission Control during connectivity loss.

Show an explicit OFFLINE/STALE label and source/time, never infer health from
silence. No persistence, secret storage, anonymous access, or cross-user cache.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite


@dataclass(frozen=True)
class LastKnownReading:
    metric: str
    value: float
    unit: str
    observed_at: str
    source_id: str
    quality: str
    verification_state: str
    age_seconds: int


@dataclass(frozen=True)
class LastKnownView:
    state: str
    subject_id: str | None
    latest_observed_at: str | None
    readings: tuple[LastKnownReading, ...]
    note: str


def _when(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("missing observed_at")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return dt.astimezone(timezone.utc)


class LastKnownCache:
    """Hold validated, scoped readings only while the same login remains valid.

    The native caller MUST invoke begin_authorized_scope after an authenticated
    server response, and revoke on logout, 401/403 or role/subject change.
    """

    def __init__(self, *, stale_after_seconds: int = 3600) -> None:
        if stale_after_seconds <= 0:
            raise ValueError("stale threshold must be positive")
        self._stale_after_seconds = stale_after_seconds
        self.revoke()

    def revoke(self) -> None:
        self._session_epoch: int | None = None
        self._subject_id: str | None = None
        self._readings: tuple[tuple, ...] = ()
        self._offline = False

    def begin_authorized_scope(self, subject_id: str, *, session_epoch: int) -> None:
        """Caller supplies a *nonsecret* session epoch, never a bearer token."""
        if isinstance(session_epoch, bool) or not isinstance(session_epoch, int) or session_epoch < 1:
            raise ValueError("invalid session epoch")
        if (not isinstance(subject_id, str) or not 1 <= len(subject_id.strip()) <= 80
                or any(ord(c) < 32 for c in subject_id)):
            raise ValueError("invalid authorized subject")
        subject_id = subject_id.strip()
        if (self._session_epoch, self._subject_id) != (session_epoch, subject_id):
            self.revoke()
            self._session_epoch, self._subject_id = session_epoch, subject_id

    def record_authenticated_snapshot(self, snapshot: object, *, session_epoch: int) -> None:
        """Capture a Q-0062-style validated snapshot, or erase on auth denial.

        A failed/mismatched snapshot is rejected atomically and not displayed.
        """
        if session_epoch != self._session_epoch or self._subject_id is None:
            self.revoke()
            raise ValueError("authenticated scope changed")
        status = getattr(snapshot, "status", None)
        if status == "DENIED":
            self.revoke()
            return
        if status not in {"READY", "UNVERIFIED", "STALE", "NO_DATA"}:
            raise ValueError("only authenticated observation responses can be cached")
        if getattr(snapshot, "subject_id", None) != self._subject_id:
            self.revoke()
            raise ValueError("subject mismatch: private cache erased")
        rows = getattr(snapshot, "measurements", None)
        if not isinstance(rows, tuple):
            raise ValueError("validated observation tuple required")
        validated: list[tuple] = []
        for item in rows:
            if getattr(item, "subject_id", None) != self._subject_id:
                self.revoke()
                raise ValueError("cross-subject observation")
            source = getattr(item, "source_id", None)
            metric = getattr(item, "metric", None)
            unit = getattr(item, "unit", None)
            quality = getattr(item, "quality", None)
            verification = getattr(item, "verification_state", None)
            val = getattr(item, "value", None)
            if (any(not isinstance(x, str) or not x.strip()
                    for x in (source, metric, unit, quality, verification))
                    or isinstance(val, bool) or not isinstance(val, (int, float))
                    or not isfinite(val)):
                raise ValueError("incomplete source or reading")
            observed = _when(getattr(item, "observed_at", None))
            validated.append((metric, float(val), unit, observed, source, quality, verification))
        self._readings = tuple(validated)
        self._offline = False

    def transport_lost(self) -> None:
        """Transport failure is not a failed authorization; keep in-session history."""
        if self._session_epoch is not None:
            self._offline = True

    def auth_error(self, http_status: int) -> None:
        if http_status in {401, 403}:
            self.revoke()

    def view(self, *, now: datetime) -> LastKnownView:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("current clock must have timezone")
        if self._subject_id is None:
            return LastKnownView("DENIED", None, None, (), "No active authorized subject")
        if not self._offline:
            return LastKnownView("NO_DATA", self._subject_id, None, (),
                                 "Live data belongs to the authenticated API view")
        if not self._readings:
            return LastKnownView("OFFLINE", self._subject_id, None, (),
                                 "OFFLINE — no previous source-backed observations")
        clock = now.astimezone(timezone.utc)
        readings = []
        for metric, val, unit, observed, source, quality, verification in self._readings:
            age = (clock - observed).total_seconds()
            if age < 0:
                # A future/incorrect clock cannot certify measurement recency.
                return LastKnownView("ERROR", self._subject_id, None, (),
                                     "Recorded time is in the future; hidden")
            readings.append(LastKnownReading(metric, val, unit, observed.isoformat(), source,
                                             "STALE" if age >= self._stale_after_seconds else quality,
                                             verification, int(age)))
        readings.sort(key=lambda item: item.age_seconds)
        newest = readings[0]
        return LastKnownView("STALE" if newest.age_seconds >= self._stale_after_seconds else "OFFLINE",
                             self._subject_id, newest.observed_at, tuple(readings),
                             "OFFLINE — cached in this authorized session only; measured-at age shown. "
                             "Not current health status or a diagnosis.")


def build_last_known_widget(view: LastKnownView, parent=None):
    """Native Qt 2D table. Not attached to a real client until UI integration."""
    from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

    root = QWidget(parent)
    layout = QVBoxLayout(root)
    label = QLabel(f"{view.state} — {view.note}")
    label.setWordWrap(True)
    label.setAccessibleName("Offline and stale provenance warning")
    layout.addWidget(label)
    table = QTableWidget(len(view.readings), 6)
    table.setAccessibleName("Last-known source-backed readings, not live health")
    table.setHorizontalHeaderLabels(["Metric", "Last measured", "Age", "Source", "Quality", "Recorded value"])
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    for i, r in enumerate(view.readings):
        values = (r.metric, r.observed_at, f"{r.age_seconds} seconds ago", r.source_id,
                  r.quality, f"{r.value:g} {r.unit}")
        for j, value in enumerate(values):
            table.setItem(i, j, QTableWidgetItem(value))
    layout.addWidget(table)
    return root
