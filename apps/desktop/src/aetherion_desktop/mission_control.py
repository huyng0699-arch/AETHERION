"""Qt Mission Control backed exclusively by authenticated AETHERION observations.

A subject is shown only when the operator explicitly requests it and the API
allows it. This prototype does not discover crew, invent telemetry, or diagnose.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from urllib.parse import urlencode


VALID_QUALITY = frozenset({"READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"})


@dataclass(frozen=True)
class ObservationRow:
    metric: str
    reading: str
    observed_at: str
    source_id: str
    scope: str
    quality: str
    verification_state: str


@dataclass(frozen=True)
class MissionSnapshot:
    state: str
    subject_id: str
    rows: tuple[ObservationRow, ...]
    latest_at: str
    note: str
    has_more: bool = False


def observation_url(api_url: str, subject_id: str) -> str:
    """Build a query without interpreting user-provided IDs as URL syntax."""
    subject_id = subject_id.strip()
    if not (1 <= len(subject_id) <= 80) or any(ord(c) < 32 for c in subject_id):
        raise ValueError("Provide a subject ID between 1 and 80 printable characters")
    return f"{api_url.rstrip('/')}/api/v1/observations?{urlencode({'subject_id': subject_id, 'limit': 100})}"


def parse_observations(payload: object, subject_id: str, *, now: datetime | None = None) -> MissionSnapshot:
    """Parse only identified, source-backed records; invalid payload fails closed."""
    if not isinstance(payload, dict) or payload.get("subject_id") != subject_id:
        return MissionSnapshot("ERROR", subject_id, (), "", "Response subject mismatch or malformed payload")
    data = payload.get("observations")
    if not isinstance(data, list):
        return MissionSnapshot("ERROR", subject_id, (), "", "Missing observations array")
    parsed: list[ObservationRow] = []
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Reference clock must have a timezone")
    for item in data:
        if not isinstance(item, dict) or item.get("subject_id") != subject_id:
            return MissionSnapshot("ERROR", subject_id, (), "", "Observation identity mismatch")
        required = ("metric", "value", "unit", "observed_at", "source_id", "scope", "quality", "verification_state")
        if any(item.get(k) is None or str(item[k]).strip() == "" for k in required):
            return MissionSnapshot("ERROR", subject_id, (), "", "Observation lacks provenance")
        try:
            value = float(item["value"])
            if not math.isfinite(value):
                raise ValueError("nonfinite")
            observed = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00"))
            if observed.tzinfo is None or observed.utcoffset() is None:
                raise ValueError("naive timestamp")
        except (ValueError, TypeError, OverflowError):
            return MissionSnapshot("ERROR", subject_id, (), "", "Invalid observation value or timestamp")
        quality = str(item["quality"]).upper()
        if quality not in VALID_QUALITY:
            quality = "UNVERIFIED"
        # Never upgrade unverified/self-reported observations to medically verified.
        verified = str(item["verification_state"])
        if quality == "READY" and verified != "VERIFIED":
            quality = "UNVERIFIED"
        if observed > now:
            quality = "UNVERIFIED"  # future data is not a clinical status
        elif (now - observed.astimezone(timezone.utc)).total_seconds() > 3600 and quality == "READY":
            quality = "STALE"
        parsed.append(ObservationRow(str(item["metric"]), f"{value:g} {item['unit']}",
                                     observed.isoformat(), str(item["source_id"]), str(item["scope"]),
                                     quality, verified))
    if not parsed:
        return MissionSnapshot("NO_DATA", subject_id, (), "", "No authenticated observations for this subject")
    parsed.sort(key=lambda r: datetime.fromisoformat(r.observed_at).timestamp(), reverse=True)
    latest = parsed[0].observed_at
    return MissionSnapshot("READY", subject_id, tuple(parsed), latest,
                           "Recorded observations only — not a medical assessment",
                           payload.get("has_more") is True)


def build_mission_control_page(api_url: str, network, parent=None):
    """Native Qt widget. Qt import is lazy so data contracts remain headlessly testable."""
    from PySide6.QtCore import Qt, QUrl
    from PySide6.QtNetwork import QNetworkRequest
    from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QLabel, QLineEdit,
        QListWidget, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

    class MissionControlPage(QWidget):
        def __init__(self):
            super().__init__(parent)
            self._token = ""  # ephemeral; never logged or saved to disk
            self._subjects: list[str] = []
            self._request_seq = 0
            lay = QVBoxLayout(self)
            title = QLabel("Mission Control · Recorded observations")
            title.setObjectName("heading")
            lay.addWidget(title)
            self.status = QLabel("OFFLINE / NOT AUTHENTICATED — no health status inferred")
            self.status.setWordWrap(True)
            lay.addWidget(self.status)
            auth = QHBoxLayout()
            self.username = QLineEdit(); self.username.setPlaceholderText("Local username")
            self.password = QLineEdit(); self.password.setPlaceholderText("Local password")
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            auth.addWidget(self.username)
            auth.addWidget(self.password)
            login = QPushButton("Sign in")
            login.clicked.connect(self.sign_in)
            auth.addWidget(login)
            lay.addLayout(auth)
            subject_row = QHBoxLayout()
            self.subject_input = QLineEdit()
            self.subject_input.setPlaceholderText("Authorized subject ID (no invented roster)")
            subject_row.addWidget(self.subject_input)
            add = QPushButton("Open subject")
            add.clicked.connect(self.add_subject)
            subject_row.addWidget(add)
            self.refresh = QPushButton("Refresh recorded data")
            self.refresh.clicked.connect(self.refresh_subject)
            subject_row.addWidget(self.refresh)
            lay.addLayout(subject_row)
            self.subjects = QListWidget()
            self.subjects.setMaximumHeight(100)
            self.subjects.currentTextChanged.connect(self.refresh_subject)
            lay.addWidget(self.subjects)
            self.latest = QLabel("NO_DATA — select an authorized subject")
            lay.addWidget(self.latest)
            self.table = QTableWidget(0, 7)
            self.table.setHorizontalHeaderLabels(["Metric", "Recorded value", "Observed at", "Source", "Scope", "Quality", "Verification"])
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.table.setAccessibleName("Recorded observations and provenance")
            lay.addWidget(self.table, 1)
            self.technical = QLabel("Technical connectivity and health observations are separate. "
                                    "No clinical events or telemetry are inferred from silence.")
            self.technical.setWordWrap(True)
            lay.addWidget(self.technical)

        def sign_in(self):
            if not self.username.text().strip() or not self.password.text():
                self.status.setText("DENIED — enter configured local credentials")
                return
            request = QNetworkRequest(QUrl(api_url.rstrip("/") + "/api/v1/auth/login"))
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
            body = json.dumps({"username": self.username.text().strip(), "password": self.password.text()}).encode()
            self.password.clear()
            reply = network.post(request, body)
            reply.finished.connect(lambda: self._signed_in(reply))

        def _signed_in(self, reply):
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            try:
                response = json.loads(bytes(reply.readAll()).decode("utf-8"))
                token = response.get("access_token") if isinstance(response, dict) else None
            except (ValueError, UnicodeDecodeError):
                token = None
            reply.deleteLater()
            if code != 200 or not isinstance(token, str) or not token:
                self._token = ""
                self.status.setText("DENIED / OFFLINE — login failed; no records shown")
                self.table.setRowCount(0)
                return
            self._token = token
            self.status.setText("Authenticated local session — choose an authorized subject")
            self.refresh_subject()

        def add_subject(self):
            subject_id = self.subject_input.text().strip()
            try:
                observation_url(api_url, subject_id)
            except ValueError:
                self.status.setText("ERROR — subject ID must be 1–80 printable characters")
                return
            if subject_id not in self._subjects:
                self._subjects.append(subject_id)
                self.subjects.addItem(subject_id)
            self.subjects.setCurrentRow(self._subjects.index(subject_id))

        def refresh_subject(self, *_):
            subject_id = self.subjects.currentItem().text() if self.subjects.currentItem() else ""
            self._request_seq += 1
            seq = self._request_seq
            self.table.setRowCount(0)
            if not subject_id:
                self.status.setText("NO_DATA — no authorized subject selected")
                return
            if not self._token:
                self.status.setText("DENIED — sign in before requesting protected observations")
                return
            url = observation_url(api_url, subject_id)
            request = QNetworkRequest(QUrl(url))
            request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
            self.status.setText(f"Loading recorded data for {subject_id}…")
            reply = network.get(request)
            reply.finished.connect(lambda: self._loaded(reply, subject_id, seq))

        def _loaded(self, reply, subject_id, seq):
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            raw = bytes(reply.readAll())
            reply.deleteLater()
            if seq != self._request_seq:
                return  # never show a superseded subject's response
            if code in (401, 403):
                self._token = "" if code == 401 else self._token
                self.status.setText("DENIED — session expired or subject access forbidden")
                self.latest.setText("No accessible observations")
                return
            if code != 200:
                self.status.setText("OFFLINE / ERROR — server unreachable or request rejected")
                self.latest.setText("No observations displayed")
                return
            try:
                snapshot = parse_observations(json.loads(raw.decode("utf-8")), subject_id)
            except (ValueError, UnicodeDecodeError):
                snapshot = MissionSnapshot("ERROR", subject_id, (), "", "Malformed JSON response")
            self.status.setText(f"{snapshot.state} — {snapshot.note}")
            self.latest.setText("Last observed: " + snapshot.latest_at if snapshot.latest_at else "No recorded measurements")
            self.table.setRowCount(len(snapshot.rows))
            for row_i, obs in enumerate(snapshot.rows):
                for col_i, value in enumerate((obs.metric, obs.reading, obs.observed_at, obs.source_id,
                                                obs.scope, obs.quality, obs.verification_state)):
                    self.table.setItem(row_i, col_i, QTableWidgetItem(value))
            if snapshot.has_more:
                self.technical.setText("More server records exist; showing the newest 100. "
                                       "No health incident verdict is available from this endpoint.")

    return MissionControlPage()
