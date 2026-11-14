"""Authenticated, source-aware native Personal Health view.

Q-0077 integrates Mission -> Personal by passing the *same explicit subject ID*
and ephemeral in-memory bearer token to the canonical HTTP API. No person,
health reading or access right is synthesized; the server is the authority.
"""
from __future__ import annotations

import json

from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from .today_dashboard import (
    build_personal_today_snapshot,
    personal_observations_url,
)


def checked_personal_handoff(subject_id: str, access_token: str) -> tuple[str, str]:
    """Validate the client handoff before network access; not authorization."""
    if not isinstance(subject_id, str):
        raise ValueError("A subject ID must be explicitly supplied")
    cleaned = subject_id.strip()
    # Apply the existing canonical URL validation, including control characters.
    personal_observations_url("http://127.0.0.1", cleaned)
    if not isinstance(access_token, str) or not access_token.strip():
        raise ValueError("An authenticated local session is required")
    if "\r" in access_token or "\n" in access_token:
        raise ValueError("Invalid session token")
    return cleaned, access_token


class AuthorizedPersonalTodayPage(QWidget):
    """Native Qt Personal Today page driven by authenticated observations."""

    def __init__(self, api_url: str, network, parent=None):
        super().__init__(parent)
        self._api_url = api_url.rstrip("/")
        self._network = network
        self._subject_id = ""
        self._token = ""
        self._request_seq = 0

        layout = QVBoxLayout(self)
        heading = QLabel("Personal Health / Today")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        self.subject_label = QLabel("No subject selected — choose a subject in Mission Control")
        self.subject_label.setAccessibleName("Exact selected crew subject")
        layout.addWidget(self.subject_label)
        self.status_label = QLabel("NO_DATA — no personal observations requested")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        controls = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh selected subject")
        self.refresh_button.clicked.connect(self.refresh)
        controls.addWidget(self.refresh_button)
        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Metric", "Recorded value", "Observed at", "Source", "Quality", "Verification"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAccessibleName("Selected person's authenticated observations")
        layout.addWidget(self.table, 1)
        self.note = QLabel(
            "No symptom form is required. Missing readings are unknown, "
            "not proof of health. NASA research is not live crew telemetry."
        )
        self.note.setWordWrap(True)
        layout.addWidget(self.note)

    @property
    def selected_subject_id(self) -> str:
        return self._subject_id

    def select_subject(self, subject_id: str, access_token: str) -> None:
        """Change subject atomically; never display the previous subject's records."""
        self._request_seq += 1  # invalidate any in-flight reply from prior subject
        self.table.setRowCount(0)
        self._subject_id = ""
        self._token = ""
        try:
            subject, token = checked_personal_handoff(subject_id, access_token)
        except ValueError:
            self.subject_label.setText("No authorized subject selected")
            self.status_label.setText("DENIED — invalid subject or missing session")
            return
        self._subject_id = subject
        self._token = token
        self.subject_label.setText(f"Subject: {subject}")
        self.status_label.setText("Loading authenticated observations…")
        self.refresh()

    def refresh(self) -> None:
        if not self._subject_id or not self._token:
            self.table.setRowCount(0)
            self.status_label.setText("DENIED — select a subject from Mission Control and sign in")
            return
        self._request_seq += 1
        seq, subject = self._request_seq, self._subject_id
        self.table.setRowCount(0)
        request = QNetworkRequest(QUrl(personal_observations_url(self._api_url, subject)))
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode("utf-8"))
        self.status_label.setText(f"Loading subject {subject} from local API…")
        reply = self._network.get(request)
        reply.finished.connect(lambda: self._on_reply(reply, subject, seq))

    def _on_reply(self, reply, subject_id: str, seq: int) -> None:
        status_code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        network_error = reply.error() != reply.NetworkError.NoError
        raw = bytes(reply.readAll())
        reply.deleteLater()
        if seq != self._request_seq or subject_id != self._subject_id:
            return  # stale/superseded reply must never expose another subject
        if status_code in (401, 403):
            self.table.setRowCount(0)
            if status_code == 401:
                self._token = ""
            snapshot = build_personal_today_snapshot(
                {}, subject_id, denied=True
            )
        elif network_error or status_code is None:
            snapshot = build_personal_today_snapshot({}, subject_id, offline=True)
        elif status_code != 200:
            self.table.setRowCount(0)
            self.status_label.setText("ERROR — server refused observations request")
            return
        else:
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                payload = {}
            snapshot = build_personal_today_snapshot(payload, subject_id)

        self.status_label.setText(f"{snapshot.state} — {snapshot.status_note}")
        self.table.setRowCount(len(snapshot.cards))
        for row, card in enumerate(snapshot.cards):
            values = (
                card.metric, card.reading, card.observed_at,
                card.source_id, card.quality, card.verification_state
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        if snapshot.has_more:
            self.note.setText(
                "More records exist on the server. Showing the latest 50, "
                "with source and verification labels."
            )
