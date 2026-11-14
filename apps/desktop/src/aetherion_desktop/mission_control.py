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

from .localization import normalize_locale, tr, translate_existing, translate_shell_widgets
from .features.mission.crew_data_state import state_from_server_response


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
    from PySide6.QtCore import Qt, QUrl, Signal
    from PySide6.QtNetwork import QNetworkRequest
    from PySide6.QtWidgets import (QFormLayout, QHBoxLayout, QLabel, QLineEdit,
        QListWidget, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

    class MissionControlPage(QWidget):
        # The token is transferred in memory only, within the same Qt process.
        subject_activated = Signal(str, str)

        def __init__(self):
            super().__init__(parent)
            self.ui_language = "vi"
            self._status_key: str | None = None
            self._status_values: dict[str, object] = {}
            self._token = ""  # ephemeral; never logged or saved to disk
            self._subjects: list[str] = []
            self._request_seq = 0
            self._login_seq = 0
            self._authorized_subject: str | None = None  # only after successful GET for that exact subject
            # A single native responsive layout, not a second server or webview.
            from .features.mission.mission_layout import install_mission_layout
            install_mission_layout(self, api_url)
            self.open_personal_button.setEnabled(False)

        def _update_summary(self, *, subject: str = "", count: int | None = None,
                            latest: str = "", sources: int | None = None):
            from .features.mission.mission_layout import update_summary
            update_summary(self, subject=subject, count=count, latest=latest, sources=sources)

        def set_locale(self, locale: str):
            """Switch presentation without logging out, discarding data or a new GET."""
            self.ui_language = normalize_locale(locale)
            translate_shell_widgets(self, self.ui_language)
            self.events_widget.set_locale(self.ui_language)
            # The observation header "Observed at" is context-dependent.
            # Semantic keys avoid an ambiguous English -> Vietnamese guess.
            self.table.setHorizontalHeaderLabels([
                tr(self.ui_language, "mission.metric"),
                tr(self.ui_language, "mission.value"),
                tr(self.ui_language, "mission.timestamp"),
                tr(self.ui_language, "mission.source"),
                tr(self.ui_language, "mission.scope"),
                tr(self.ui_language, "mission.quality"),
                tr(self.ui_language, "mission.verification"),
            ])
            if self._status_key:
                self._say(self._status_key, **self._status_values)

        def _say(self, key: str, **values):
            # Keep the original format arguments; they can be rendered again
            # after changing locale, including in-flight HTTP response states.
            self._status_key = key
            self._status_values = dict(values)
            localized = dict(values)
            if key == "mission.snapshot" and "note" in localized:
                localized["note"] = translate_existing(
                    str(localized["note"]), self.ui_language
                )
            self.status.setText(tr(self.ui_language, key, **localized))

        def sign_in(self):
            # A new attempt invalidates earlier data and outstanding GET/login
            # callbacks. A failed login may never leave a prior session active.
            self._login_seq += 1
            seq = self._login_seq
            self._request_seq += 1
            self._token = ""
            self._authorized_subject = None
            self.open_personal_button.setEnabled(False)
            # Do not leak prior account's selected subject IDs into the next
            # session, even when the new login fails or the server is offline.
            self._subjects.clear()
            self.subjects.clear()
            self.subject_input.clear()
            self.table.setRowCount(0)
            self.technical.setText(tr(self.ui_language, "mission.technicalDisclaimer"))
            self._update_summary()
            if not self.username.text().strip() or not self.password.text():
                self._say("mission.deniedCredentials")
                return
            request = QNetworkRequest(QUrl(api_url.rstrip("/") + "/api/v1/auth/login"))
            request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
            body = json.dumps({"username": self.username.text().strip(), "password": self.password.text()}).encode()
            self.password.clear()
            reply = network.post(request, body)
            reply.finished.connect(lambda: self._signed_in(reply, seq))

        def _signed_in(self, reply, seq):
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            raw = bytes(reply.readAll())
            reply.deleteLater()
            if seq != self._login_seq:
                return  # a superseded login cannot revive an older session
            try:
                response = json.loads(raw.decode("utf-8"))
                token = response.get("access_token") if isinstance(response, dict) else None
            except (ValueError, UnicodeDecodeError):
                token = None
            if code != 200 or not isinstance(token, str) or not token:
                self._token = ""
                self._authorized_subject = None
                self._say("mission.loginFailed")
                self.table.setRowCount(0)
                self._update_summary()
                return
            self._token = token
            self._say("mission.authenticated")
            self.refresh_subject()

        def add_subject(self):
            subject_id = self.subject_input.text().strip()
            try:
                observation_url(api_url, subject_id)
            except ValueError:
                self._say("mission.invalidSubject")
                return
            if subject_id not in self._subjects:
                self._subjects.append(subject_id)
                self.subjects.addItem(subject_id)
            self.subjects.setCurrentRow(self._subjects.index(subject_id))

        def open_selected_personal(self):
            """Never route to a guessed subject or silently reuse a logged-out session."""
            selected = self.subjects.currentItem()
            if selected is None:
                self._say("mission.selectBeforeOpen")
                return
            if not self._token:
                self._say("mission.deniedOpen")
                return
            # A manually entered subject is not authorized merely because login
            # worked. Require a successful authenticated GET for the same ID.
            if self._authorized_subject != selected.text():
                self._say("mission.expired")
                return
            self.subject_activated.emit(selected.text(), self._token)

        def refresh_subject(self, *_):
            subject_id = self.subjects.currentItem().text() if self.subjects.currentItem() else ""
            self._request_seq += 1
            seq = self._request_seq
            self._authorized_subject = None  # handoff disabled until this exact GET is accepted
            self.open_personal_button.setEnabled(False)
            self.table.setRowCount(0)
            self.technical.setText(tr(self.ui_language, "mission.technicalDisclaimer"))
            self._update_summary(subject=subject_id)
            if not subject_id:
                self._say("mission.noSubject")
                return
            if not self._token:
                self._say("mission.loginRequired")
                return
            url = observation_url(api_url, subject_id)
            request = QNetworkRequest(QUrl(url))
            request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode())
            self._say("mission.loading", subject=subject_id)
            reply = network.get(request)
            reply.finished.connect(lambda: self._loaded(reply, subject_id, seq))

        def _loaded(self, reply, subject_id, seq):
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            raw = bytes(reply.readAll())
            reply.deleteLater()
            if seq != self._request_seq:
                return  # switching subjects must discard old server responses
            self._authorized_subject = None
            if code in (401, 403):
                if code == 401:
                    self._token = ""
                self._say("mission.expired")
                self.table.setRowCount(0)
                self._update_summary(subject=subject_id)
                return
            if code != 200:
                self._say("mission.offline")
                self.table.setRowCount(0)
                self._update_summary(subject=subject_id)
                return
            try:
                data = state_from_server_response(
                    subject_id, 200, json.loads(raw.decode("utf-8"))
                )
            except (ValueError, UnicodeDecodeError, TypeError):
                self._say("mission.snapshot", state="ERROR",
                          note=tr(self.ui_language, "mission.note.malformed"))
                self.table.setRowCount(0)
                self._update_summary(subject=subject_id)
                return

            # The strict adapter refuses mixed identities, missing receipt times,
            # non-finite numbers, and research/engineering fixtures as telemetry.
            if data.status in {"ERROR", "DENIED", "OFFLINE"}:
                self._say("mission.snapshot", state=data.status,
                          note=tr(self.ui_language, "mission.note.badValue"))
                self.table.setRowCount(0)
                self._update_summary(subject=subject_id)
                return

            # NO_DATA is a successful authorized read, not proof of health.
            self._authorized_subject = subject_id
            self.open_personal_button.setEnabled(True)
            note_key = ("mission.note.noObservations" if data.status == "NO_DATA"
                        else "mission.note.recorded")
            self._say("mission.snapshot", state=data.status,
                      note=tr(self.ui_language, note_key))
            self._update_summary(
                subject=subject_id, count=len(data.measurements),
                latest=data.last_observed_at or "",
                sources=len({row.source_id for row in data.measurements}),
            )
            self.table.setRowCount(len(data.measurements))
            for row_i, obs in enumerate(data.measurements):
                values = (obs.metric, f"{obs.value:g} {obs.unit}", obs.observed_at,
                          obs.source_id, obs.scope, obs.quality, obs.verification_state)
                for col_i, value in enumerate(values):
                    self.table.setItem(row_i, col_i, QTableWidgetItem(value))
            if data.has_more:
                self.technical.setText(tr(self.ui_language, "mission.more"))

    return MissionControlPage()
