"""Bilingual native symptom interview with explicit, authenticated Care handoff.

An optional user-initiated workflow, not an autonomous diagnostic service.
Red-flag reports end the ordinary interview and offer immediate human help.
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote

from PySide6.QtCore import Qt, QUrl, QUrlQuery, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from .localization import normalize_locale, tr


class SymptomInterviewPage(QWidget):
    care_created = Signal(str)
    authorization_requested = Signal()

    def __init__(self, parent=None, api_url: str | None = None, locale: str = "vi"):
        super().__init__(parent)
        self.setObjectName("aetherionSymptomInterview")
        self.api_url = (api_url or os.environ.get(
            "AETHERION_API_URL", "http://127.0.0.1:8765")).rstrip("/")
        self.net = QNetworkAccessManager(self)
        self.locale = normalize_locale(locale)
        self.subject_id = ""
        self.token = ""
        self.answers: dict[str, str] = {}
        self.active_symptoms: list[str] = []
        self._en_labels: dict[str, str] = {}
        self._last_question_response: dict = {}
        self.question_id: str | None = None
        self.last_state = ""
        self._saving = False
        self._request_generation = 0
        self._search_seq = 0  # discard out-of-order matches from earlier queries
        self._question_seq = 0  # discard out-of-order adaptive question replies

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 20, 26, 20)
        root.setSpacing(12)
        self.title = QLabel()
        self.title.setObjectName("heading")
        root.addWidget(self.title)
        self.notice = QLabel()
        self.notice.setWordWrap(True)
        root.addWidget(self.notice)
        self.identity = QLabel()
        self.identity.setWordWrap(True)
        root.addWidget(self.identity)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setMaxLength(200)
        self.search.returnPressed.connect(self.find)
        search_row.addWidget(self.search, 1)
        self.find_button = QPushButton()
        self.find_button.clicked.connect(self.find)
        search_row.addWidget(self.find_button)
        root.addLayout(search_row)
        self.hits = QListWidget()
        self.hits.setMaximumHeight(120)
        self.hits.itemClicked.connect(self.select_symptom)
        self.hits.itemActivated.connect(self.select_symptom)  # Enter / keyboard activation
        root.addWidget(self.hits)
        self.selection = QLabel()
        self.selection.setTextFormat(Qt.TextFormat.PlainText)
        self.selection.setWordWrap(True)
        root.addWidget(self.selection)

        self.question = QLabel()
        self.question.setTextFormat(Qt.TextFormat.PlainText)
        self.question.setObjectName("heroCopy")
        self.question.setWordWrap(True)
        root.addWidget(self.question)
        self.answers_box = QComboBox()
        self.answers_box.setMinimumHeight(38)
        root.addWidget(self.answers_box)

        choices = QHBoxLayout()
        self.use_ai = QCheckBox()
        self.use_ai.setChecked(False)
        choices.addWidget(self.use_ai)
        self.allow_cloud = QCheckBox()
        self.allow_cloud.setChecked(False)
        self.allow_cloud.setEnabled(False)
        self.use_ai.toggled.connect(self._toggle_ai)
        choices.addWidget(self.allow_cloud)
        root.addLayout(choices)

        actions = QHBoxLayout()
        self.next_button = QPushButton()
        self.next_button.setObjectName("primaryAction")
        self.next_button.clicked.connect(self.advance)
        actions.addWidget(self.next_button)
        self.undo_button = QPushButton()
        self.undo_button.clicked.connect(self.undo)
        actions.addWidget(self.undo_button)
        self.summary_button = QPushButton()
        self.summary_button.clicked.connect(self.show_summary)
        actions.addWidget(self.summary_button)
        root.addLayout(actions)

        consent = QHBoxLayout()
        self.consent = QCheckBox()
        self.consent.setChecked(False)
        self.consent.toggled.connect(self._update_buttons)
        consent.addWidget(self.consent, 1)
        self.save_button = QPushButton()
        self.save_button.clicked.connect(self.create_care_episode)
        consent.addWidget(self.save_button)
        root.addLayout(consent)

        footer = QHBoxLayout()
        self.new_button = QPushButton()
        self.new_button.clicked.connect(self.reset_interview)
        footer.addWidget(self.new_button)
        self.authorize_button = QPushButton()
        self.authorize_button.clicked.connect(self.authorization_requested.emit)
        footer.addWidget(self.authorize_button)
        self.help_button = QPushButton()
        self.help_button.clicked.connect(self.show_safety)
        footer.addWidget(self.help_button)
        footer.addStretch()
        root.addLayout(footer)

        self.state = QLabel()
        self.state.setTextFormat(Qt.TextFormat.PlainText)
        self.state.setWordWrap(True)
        root.addWidget(self.state)
        root.addStretch(1)
        self.set_locale(self.locale)
        self.reset_interview()

    def _s(self, key: str, **kwargs) -> str:
        return tr(self.locale, "care." + key, **kwargs)

    def set_locale(self, locale: str) -> None:
        self.locale = normalize_locale(locale)
        self.title.setText(self._s("intake.title"))
        self.notice.setText(self._s("intake.notice"))
        self.search.setPlaceholderText(self._s("intake.search"))
        self.search.setAccessibleName(self._s("intake.search"))
        self.find_button.setText(self._s("intake.find"))
        self.hits.setAccessibleName(self._s("intake.hits"))
        self.answers_box.setAccessibleName(self._s("intake.answer"))
        self.use_ai.setText(self._s("intake.ai"))
        self.allow_cloud.setText(self._s("intake.cloud"))
        self.next_button.setText(self._s("intake.next"))
        self.undo_button.setText(self._s("intake.undo"))
        self.summary_button.setText(self._s("intake.summary"))
        self.save_button.setText(self._s("intake.save"))
        self.consent.setText(self._s("intake.consent"))
        self.new_button.setText(self._s("intake.restart"))
        self.authorize_button.setText(self._s("intake.authorize"))
        self.help_button.setText(self._s("help.button"))
        self._identity_label()
        for index in range(self.hits.count()):
            item = self.hits.item(index)
            source = str(item.data(Qt.ItemDataRole.UserRole) or "")
            item.setText(self._display_symptom(source))
            item.setToolTip(
                self._s("intake.translation_note")
                if self.locale == "en" and source in self._en_labels else ""
            )
        self._selection_label()
        self._update_buttons()
        if self.question_id:
            self.question.setText(self._s("question." + self.question_id))
            for index in range(self.answers_box.count()):
                answer_code = str(self.answers_box.itemData(index) or "").lower()
                try:
                    self.answers_box.setItemText(index, self._s("answer." + answer_code))
                except KeyError:
                    # Never invent an answer label for an unknown backend code.
                    pass
        elif self.last_state:
            state_key = ("intake.finished" if self.last_state == "INTAKE_COMPLETED_UNVALIDATED"
                         else "intake.unvalidated")
            self.question.setText(self._s(state_key))
        if self.last_state:
            self._render_state(self._last_question_response)

    def _identity_label(self):
        self.identity.setText(
            self._s("intake.subject", subject=self.subject_id) if self.subject_id and self.token
            else self._s("intake.no_subject"))

    def _display_symptom(self, source_name: str) -> str:
        """Show bilingual draft terminology, retain canonical VI identifier."""
        english = self._en_labels.get(source_name)
        if self.locale == "en" and english:
            return f"{english} · {source_name}"
        return source_name

    def _selection_label(self):
        shown = [self._display_symptom(name) for name in self.active_symptoms]
        self.selection.setText(
            self._s("intake.selected", symptoms=", ".join(shown))
            if shown else self._s("intake.choose"))

    def set_identity(self, subject_id: str, access_token: str):
        # Different subjects must NEVER share draft answers, consent or visible notes.
        if subject_id != self.subject_id or access_token != self.token:
            self.reset_interview()
        self.subject_id = subject_id if access_token else ""
        self.token = access_token if subject_id else ""
        self._identity_label()
        self._update_buttons()

    def _toggle_ai(self, enabled: bool):
        self.allow_cloud.setEnabled(bool(enabled))
        if not enabled:
            self.allow_cloud.setChecked(False)

    def _update_buttons(self, *_):
        if not hasattr(self, "save_button"):
            return
        self.save_button.setEnabled(bool(
            self.token and self.subject_id and self.active_symptoms
            and self.consent.isChecked() and not self._saving
        ))
        self.next_button.setEnabled(bool(
            self.active_symptoms and self.question_id
            and self.last_state != "WITNESSED_RED_FLAG_REPORTED"
        ))

    def reset_interview(self):
        self._request_generation += 1
        self._search_seq += 1
        self._question_seq += 1
        self.active_symptoms = []
        self.answers = {}
        self._en_labels.clear()
        self._last_question_response = {}
        self.question_id = None
        self.last_state = ""
        self._saving = False
        self.hits.clear()
        self.search.clear()
        self.answers_box.clear()
        self.question.setText("")
        self.consent.setChecked(False)
        self._selection_label()
        self.state.setText(self._s("intake.not_saved"))
        self._update_buttons()

    def _request(self, method: str, route: str, payload: dict | None, callback, *,
                 authorized: bool = False):
        if authorized and not self.token:
            self.state.setText(self._s("intake.no_subject"))
            return
        request = QNetworkRequest(QUrl(self.api_url + route))
        request.setRawHeader(b"Content-Type", b"application/json")
        if authorized:
            request.setRawHeader(
                b"Authorization", ("Bearer " + self.token).encode("utf-8"))
        generation = self._request_generation
        if method == "POST":
            reply = self.net.post(request, json.dumps(
                payload or {}, ensure_ascii=False).encode("utf-8"))
        else:
            reply = self.net.get(request)

        def finished():
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            try:
                body = json.loads(bytes(reply.readAll()).decode("utf-8"))
            except (ValueError, UnicodeError):
                body = {}
            error = reply.errorString() if reply.error() else ""
            if (code or 0) >= 400:
                error = str(body.get("detail", error or code))
            reply.deleteLater()
            if generation != self._request_generation:
                return
            if code == 401:
                self.token = ""
                self._identity_label()
                self._update_buttons()
            callback(body, error)
        reply.finished.connect(finished)

    def find(self):
        # Never let an older response replace newer source-backed suggestions.
        query_text = self.search.text().strip()
        self._search_seq += 1
        seq = self._search_seq
        self.hits.clear()
        if not query_text:
            self.state.setText(self._s("intake.choose"))
            return
        self.state.setText(self._s("intake.search"))
        query = QUrlQuery()
        query.addQueryItem("query", query_text)
        query.addQueryItem("limit", "25")
        self._request(
            "GET", "/api/v1/knowledge/symptoms?" + query.toString(), None,
            lambda body, error: self._show_hits(body, error, seq, query_text),
        )

    def _show_hits(self, body, error, seq: int, searched: str):
        if seq != self._search_seq or searched != self.search.text().strip():
            return  # a superseded/edited query has no authority over the view
        self.hits.clear()
        if error or not isinstance(body, dict) or not isinstance(body.get("items"), list):
            self.state.setText(self._s("intake.error") + (" " + error if error else ""))
            return
        count = 0
        for row in body["items"][:25]:
            if not isinstance(row, dict):
                continue
            name = row.get("name")
            # Display ONLY actual names supplied by the 819-entry source API.
            # Never turn None, arbitrary objects or empty labels into symptoms.
            if not isinstance(name, str) or not name.strip() or len(name) > 120:
                continue
            canonical = name.strip()
            candidate = row.get("name_en")
            if (row.get("translation_review_state") == "UNREVIEWED_TERMINOLOGY"
                    and isinstance(candidate, str) and 0 < len(candidate) <= 140):
                self._en_labels[canonical] = candidate.strip()
            item = QListWidgetItem(self._display_symptom(canonical))
            item.setData(Qt.ItemDataRole.UserRole, canonical)
            if self.locale == "en" and canonical in self._en_labels:
                item.setToolTip(self._s("intake.translation_note"))
            self.hits.addItem(item)
            count += 1
        reported = body.get("matched")
        matches = reported if isinstance(reported, int) and not isinstance(reported, bool) and reported >= count else count
        self.state.setText(self._s("intake.matched", count=matches))

    def select_symptom(self, item):
        value = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(value, str) or not value.strip() or len(value) > 120:
            self.state.setText(self._s("intake.unknown"))
            return
        text = value.strip()
        if text not in self.active_symptoms and len(self.active_symptoms) < 20:
            self.active_symptoms.append(text)
        self.answers.clear()
        self.question_id = None
        self._selection_label()
        self._ask()

    def advance(self):
        if self.question_id and self.answers_box.currentData() is not None:
            self.answers[self.question_id] = str(self.answers_box.currentData())
        self._ask()

    def undo(self):
        if self.answers:
            self.answers.pop(next(reversed(self.answers)))
        self._ask()

    def _ask(self):
        if not self.active_symptoms:
            self.state.setText(self._s("intake.choose"))
            return
        payload = {"symptoms": self.active_symptoms,
                   "answers": self.answers,
                   "use_ai": self.use_ai.isChecked(),
                   "allow_cloud": self.allow_cloud.isChecked()}
        self._question_seq += 1
        seq = self._question_seq
        self._request("POST", "/api/v1/knowledge/interview/next",
                      payload, lambda data, error: self._show_question(
                          data, error) if seq == self._question_seq else None)

    def _show_question(self, data, error):
        if error or not isinstance(data, dict):
            self.state.setText(self._s("intake.error") + " " + error)
            return
        self.last_state = str(data.get("state", ""))
        self._last_question_response = data
        self.answers_box.clear()
        question = data.get("next_question")
        candidate = question.get("id") if isinstance(question, dict) else None
        self.question_id = candidate if isinstance(candidate, str) and len(candidate) <= 80 else None
        if self.question_id:
            options = question.get("answers")
            try:
                translated_question = self._s("question." + self.question_id)
                if not isinstance(options, list) or len(options) > 12:
                    raise KeyError("Invalid question option list")
                translated_options = []
                for option in options:
                    if not isinstance(option, str) or len(option) > 40:
                        raise KeyError("Unexpected answer code")
                    translated_options.append((self._s("answer." + option.lower()), option))
            except KeyError:
                # The backend is authoritative for answer codes; unknown codes
                # are NOT guessed, translated or offered as validated medicine.
                self.question_id = None
                self.question.setText(self._s("intake.unvalidated"))
                self.state.setText(self._s("intake.invalid"))
                self._update_buttons()
                return
            self.question.setText(translated_question)
            for label, code in translated_options:
                self.answers_box.addItem(label, code)
        else:
            state_key = ("intake.finished" if self.last_state == "INTAKE_COMPLETED_UNVALIDATED"
                         else "intake.unvalidated")
            self.question.setText(self._s(state_key))
        self._render_state(data)
        self._update_buttons()
        if self.last_state == "WITNESSED_RED_FLAG_REPORTED":
            self.show_safety()

    def _render_state(self, data=None):
        data = data or {}
        message_key = {
            "WITNESSED_RED_FLAG_REPORTED": "intake.redflag",
            "AMBIGUOUS_SYMPTOM": "intake.ambiguous",
            "UNKNOWN_SYMPTOM": "intake.unknown",
            "INVALID_ANSWER": "intake.invalid",
            "INTAKE_COMPLETED_UNVALIDATED": "intake.finished",
        }.get(self.last_state, "intake.unvalidated")
        self.state.setText(self._s(message_key))
        if self.last_state == "AMBIGUOUS_SYMPTOM":
            choices = [", ".join(item.get("candidates", []))
                       for item in data.get("ambiguous", [])]
            if choices:
                self.state.setText(self._s(message_key) + " " + "; ".join(choices))

    def show_summary(self):
        rows = [self._display_symptom(name) for name in self.active_symptoms]
        rows += [key + ": " + value for key, value in self.answers.items()]
        QMessageBox.information(self, self._s("intake.summary"),
                                "\n".join(rows) or self._s("intake.choose"))

    def create_care_episode(self):
        if not (self.subject_id and self.token and self.consent.isChecked()
                and self.active_symptoms):
            self.state.setText(self._s("intake.no_subject"))
            return
        if self._saving:
            return
        self._saving = True
        self._update_buttons()
        payload = {
            "subject_id": self.subject_id,
            "chief_concern": ", ".join(self.active_symptoms)[:500],
            "symptom_terms": self.active_symptoms,
            "interview_answers": self.answers,
            "explicit_consent": True,
        }
        self._request("POST", "/api/v1/care/episodes", payload, self._created,
                      authorized=True)

    def _created(self, data, error):
        self._saving = False
        self._update_buttons()
        episode = data.get("episode") if isinstance(data, dict) else None
        if error or not isinstance(episode, dict) or episode.get("subject_id") != self.subject_id:
            self.state.setText(self._s("intake.error") + " " + error)
            return
        self.state.setText(self._s("intake.saved"))
        self.consent.setChecked(False)
        self.care_created.emit(str(episode.get("episode_id", "")))

    def show_safety(self):
        QMessageBox.warning(self, self._s("help.button"), self._s("help.notice"))


def build_symptom_interview(parent=None) -> SymptomInterviewPage:
    return SymptomInterviewPage(parent)
