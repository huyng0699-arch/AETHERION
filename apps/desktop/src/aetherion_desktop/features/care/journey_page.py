"""Native, bilingual and server-backed care journey (GATHER/EVALUATE/ACT/RECHECK).

No synthetic health values. User confirmation is required to record any action.
A session and authorized subject are passed only from the existing Mission UI.
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote

from PySide6.QtCore import Qt, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ...localization import normalize_locale, tr


class CareJourneyPage(QWidget):
    """A persistent timeline, never an automatic clinical action engine."""

    def __init__(self, parent=None, *, api_url: str | None = None, locale: str = "vi"):
        super().__init__(parent)
        self.setObjectName("aetherionCareJourney")
        self.api_url = (api_url or os.environ.get(
            "AETHERION_API_URL", "http://127.0.0.1:8765")).rstrip("/")
        self.net = QNetworkAccessManager(self)
        self.locale = normalize_locale(locale)
        self.subject_id = ""
        self.token = ""
        self.episode_id = ""
        self.phase = ""
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(12)

        self.title = QLabel()
        self.title.setObjectName("heading")
        root.addWidget(self.title)
        self.identity = QLabel()
        self.identity.setWordWrap(True)
        root.addWidget(self.identity)

        controls = QHBoxLayout()
        self.refresh_button = QPushButton()
        self.refresh_button.clicked.connect(self.refresh)
        controls.addWidget(self.refresh_button)
        self.help_button = QPushButton()
        self.help_button.clicked.connect(self.show_safety)
        controls.addWidget(self.help_button)
        controls.addStretch()
        root.addLayout(controls)

        self.episodes_label = QLabel()
        root.addWidget(self.episodes_label)
        self.episodes = QListWidget()
        self.episodes.setMaximumHeight(135)
        self.episodes.currentItemChanged.connect(self._episode_selected)
        root.addWidget(self.episodes)

        self.phase_label = QLabel()
        self.phase_label.setObjectName("heroCopy")
        root.addWidget(self.phase_label)
        self.notice = QLabel()
        self.notice.setWordWrap(True)
        root.addWidget(self.notice)

        form = QFormLayout()
        self.summary_label = QLabel()
        self.summary = QLineEdit()
        self.summary.setMaxLength(1000)
        form.addRow(self.summary_label, self.summary)
        self.action_label = QLabel()
        self.action = QComboBox()
        self.action.addItem("", None)
        self.action.addItem("DONE", "DONE")
        self.action.addItem("NOT_DONE", "NOT_DONE")
        self.action.addItem("CANNOT_DO", "CANNOT_DO")
        form.addRow(self.action_label, self.action)
        self.outcome_label = QLabel()
        self.outcome = QComboBox()
        self.outcome.addItem("", None)
        self.outcome.addItem("BETTER", "BETTER")
        self.outcome.addItem("UNCHANGED", "UNCHANGED")
        self.outcome.addItem("WORSE", "WORSE")
        self.outcome.addItem("UNKNOWN", "UNKNOWN")
        form.addRow(self.outcome_label, self.outcome)
        root.addLayout(form)

        steps = QHBoxLayout()
        self.advance_button = QPushButton()
        self.advance_button.setObjectName("primaryAction")
        self.advance_button.clicked.connect(self.advance)
        steps.addWidget(self.advance_button)
        self.reassess_button = QPushButton()
        self.reassess_button.clicked.connect(self.reassess)
        steps.addWidget(self.reassess_button)
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.close_episode)
        steps.addWidget(self.close_button)
        steps.addStretch()
        root.addLayout(steps)

        self.events_label = QLabel()
        root.addWidget(self.events_label)
        self.events = QListWidget()
        root.addWidget(self.events, 1)
        self.status = QLabel()
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.set_locale(self.locale)
        self._reset()

    def _s(self, key: str, **kwargs) -> str:
        return tr(self.locale, "care." + key, **kwargs)

    def set_locale(self, locale: str) -> None:
        self.locale = normalize_locale(locale)
        self.title.setText(self._s("journey.title"))
        self.refresh_button.setText(self._s("journey.refresh"))
        self.help_button.setText(self._s("help.button"))
        self.episodes_label.setText(self._s("journey.episodes"))
        self.notice.setText(self._s("journey.notice"))
        self.summary_label.setText(self._s("journey.summary"))
        self.action_label.setText(self._s("journey.action"))
        self.outcome_label.setText(self._s("journey.outcome"))
        self.events_label.setText(self._s("journey.events"))
        self.reassess_button.setText(self._s("journey.reassess"))
        self.close_button.setText(self._s("journey.close"))
        for i, key in enumerate(("select", "done", "not_done", "cannot")):
            self.action.setItemText(i, self._s("action." + key))
        for i, key in enumerate(("select", "better", "unchanged", "worse", "unknown")):
            self.outcome.setItemText(i, self._s("outcome." + key))
        self._update_controls()

    def set_identity(self, subject_id: str, access_token: str) -> None:
        """Switching subject destroys all previously displayed private episode data."""
        if not subject_id or not access_token:
            self.subject_id, self.token = "", ""
            self._reset()
            return
        changed = subject_id != self.subject_id or access_token != self.token
        self.subject_id, self.token = subject_id, access_token
        if changed:
            self._reset()
        self._update_controls()
        self.refresh()

    def _reset(self) -> None:
        self.episode_id, self.phase = "", ""
        self.episodes.clear()
        self.events.clear()
        self.summary.clear()
        self.action.setCurrentIndex(0)
        self.outcome.setCurrentIndex(0)
        self.status.setText(self._s("journey.unknown"))
        self._update_controls()

    def _update_controls(self) -> None:
        if not hasattr(self, "identity"):
            return
        authenticated = bool(self.subject_id and self.token)
        self.identity.setText(
            self._s("journey.subject", subject=self.subject_id)
            if authenticated else self._s("journey.no_subject"))
        self.phase_label.setText(
            self._s("journey.phase", phase=self.phase or "-"))
        next_phase = {"GATHER": "EVALUATE", "EVALUATE": "ACT",
                      "ACT": "RECHECK"}.get(self.phase)
        self.advance_button.setText(
            self._s("journey.advance", phase=next_phase or "-"))
        self.advance_button.setEnabled(authenticated and bool(next_phase))
        self.reassess_button.setEnabled(authenticated and self.phase == "RECHECK")
        self.close_button.setEnabled(authenticated and self.phase == "RECHECK")
        self.refresh_button.setEnabled(authenticated)
        self.action.setEnabled(self.phase == "EVALUATE")
        self.outcome.setEnabled(self.phase == "ACT")

    def _request(self, method: str, route: str, payload: dict | None, callback) -> None:
        if not self.token or not self.subject_id:
            self.status.setText(self._s("journey.no_subject"))
            return
        request = QNetworkRequest(QUrl(self.api_url + route))
        request.setRawHeader(b"Authorization", ("Bearer " + self.token).encode("utf-8"))
        request.setRawHeader(b"Content-Type", b"application/json")
        if method == "POST":
            reply = self.net.post(
                request, json.dumps(payload or {}, ensure_ascii=False).encode("utf-8"))
        else:
            reply = self.net.get(request)

        def finished():
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            try:
                body = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except (ValueError, UnicodeError):
                body = {}
            err = reply.errorString() if reply.error() or not (200 <= (code or 0) < 300) else ""
            reply.deleteLater()
            if code == 401:
                self.token = ""
                self._reset()
            callback(body, err or (str(body.get("detail", "")) if (code or 0) >= 400 else ""))
        reply.finished.connect(finished)

    def refresh(self) -> None:
        if not (self.subject_id and self.token):
            self._update_controls()
            return
        self.status.setText(self._s("journey.loading"))
        self._request("GET", "/api/v1/care/episodes?subject_id=" + quote(
            self.subject_id, safe=""), None, self._got_list)

    def _got_list(self, data: dict, error: str) -> None:
        if error or data.get("subject_id") != self.subject_id:
            self.status.setText(self._s("journey.error") + " " + error)
            return
        self.episodes.blockSignals(True)
        self.episodes.clear()
        for ep in data.get("episodes", []):
            item = QListWidgetItem(
                ep.get("created_at_utc", "")[:16] + " · " + ep.get("chief_concern", ""))
            item.setData(Qt.ItemDataRole.UserRole, ep.get("episode_id"))
            self.episodes.addItem(item)
        self.episodes.blockSignals(False)
        if self.episode_id:
            for index in range(self.episodes.count()):
                if self.episodes.item(index).data(Qt.ItemDataRole.UserRole) == self.episode_id:
                    self.episodes.setCurrentRow(index)
                    break
        self.status.setText(self._s("journey.count", count=self.episodes.count()))

    def _episode_selected(self, current, _previous) -> None:
        if current:
            self.open_episode(str(current.data(Qt.ItemDataRole.UserRole)))

    def open_episode(self, episode_id: str) -> None:
        if not episode_id or not self.subject_id:
            return
        self._request("GET", "/api/v1/care/episodes/" + quote(episode_id, safe=""),
                      None, self._got_episode)

    def _got_episode(self, data: dict, error: str) -> None:
        ep = data.get("episode")
        if error or not isinstance(ep, dict) or ep.get("subject_id") != self.subject_id:
            self.status.setText(self._s("journey.error") + " " + error)
            return
        self.episode_id = ep.get("episode_id", "")
        self.phase = ep.get("current_phase", "")
        self.events.clear()
        for event in ep.get("events", []):
            text = event.get("recorded_at_utc", "")[:16] + " · "
            text += event.get("phase", "") + " · " + event.get("summary", "")
            self.events.addItem(text)
        self.status.setText(self._s("journey.loaded"))
        self._update_controls()

    def start_from_interview(self, episode_id: str) -> None:
        """Navigate here after a separately authenticated, consensual POST."""
        if self.subject_id and self.token:
            self.open_episode(episode_id)
            self.refresh()

    def advance(self) -> None:
        next_phase = {"GATHER": "EVALUATE", "EVALUATE": "ACT",
                      "ACT": "RECHECK"}.get(self.phase)
        if next_phase:
            self._submit(next_phase)

    def reassess(self) -> None:
        if self.phase == "RECHECK":
            self._submit("GATHER")

    def close_episode(self) -> None:
        if self.phase == "RECHECK":
            self._submit("CLOSED")

    def _submit(self, next_phase: str) -> None:
        if not self.episode_id or not self.token:
            return
        summary = self.summary.text().strip()
        if not summary:
            self.status.setText(self._s("journey.summary_required"))
            return
        payload = {"next_phase": next_phase, "summary": summary, "human_confirmed": True}
        if next_phase == "ACT":
            if self.action.currentData() is None:
                self.status.setText(self._s("journey.action_required"))
                return
            payload["action_status"] = self.action.currentData()
        if next_phase == "RECHECK":
            if self.outcome.currentData() is None:
                self.status.setText(self._s("journey.outcome_required"))
                return
            payload["outcome"] = self.outcome.currentData()
        self._request("POST", "/api/v1/care/episodes/" + quote(self.episode_id, safe="") +
                      "/advance", payload, self._saved)

    def _saved(self, data: dict, error: str) -> None:
        if error:
            self.status.setText(self._s("journey.error") + " " + error)
            return
        self.summary.clear()
        self.action.setCurrentIndex(0)
        self.outcome.setCurrentIndex(0)
        self._got_episode(data, "")
        self.refresh()

    def show_safety(self) -> None:
        QMessageBox.warning(self, self._s("help.button"), self._s("help.notice"))
