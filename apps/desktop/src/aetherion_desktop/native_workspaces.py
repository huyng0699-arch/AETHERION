"""AETHERION native Monitoring, symptom question and Care workspaces.

Displays only response-validated Server observations/knowledge. Never invents
waveforms, records, clinical decisions, or persistence. No QtWebEngine needed.
The three views use semantic VI/EN UI keys in i18n/*.json.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import math
from urllib.parse import urlencode

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .localization import normalize_locale, tr


@dataclass(frozen=True)
class RecordedPoint:
    metric: str
    value: float
    unit: str
    observed_at: datetime
    source_id: str
    scope: str
    quality: str
    verification: str


def parse_recorded_observations(payload: object, subject_id: str) -> tuple[list[RecordedPoint], bool]:
    """Reject a whole response with ambiguous subject/provenance; no clinical classification."""
    if not isinstance(payload, dict) or payload.get("subject_id") != subject_id:
        raise ValueError("subject mismatch")
    rows = payload.get("observations")
    if not isinstance(rows, list) or len(rows) > 500:
        raise ValueError("invalid observations")
    accepted = []
    for item in rows:
        if not isinstance(item, dict) or item.get("subject_id") != subject_id:
            raise ValueError("identity mismatch")
        for key in ("metric", "value", "unit", "observed_at", "source_id", "scope", "quality", "verification_state"):
            if item.get(key) is None or str(item[key]).strip() == "":
                raise ValueError("missing provenance")
        number = float(item["value"])
        if not math.isfinite(number):
            raise ValueError("non-finite reading")
        observed = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00"))
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise ValueError("timestamp has no timezone")
        quality = str(item["quality"]).upper()
        if quality not in {"READY", "STALE", "UNVERIFIED", "NO_DATA", "OFFLINE", "DENIED", "ERROR"}:
            quality = "UNVERIFIED"
        if observed > datetime.now(timezone.utc):
            quality = "UNVERIFIED"
        if quality == "READY" and item["verification_state"] != "VERIFIED":
            quality = "UNVERIFIED"
        accepted.append(RecordedPoint(str(item["metric"]), number, str(item["unit"]), observed,
                                      str(item["source_id"]), str(item["scope"]),
                                      quality, str(item["verification_state"])))
    accepted.sort(key=lambda x: x.observed_at, reverse=True)
    return accepted, payload.get("has_more") is True


def _panel() -> tuple[QFrame, QVBoxLayout]:
    panel = QFrame()
    panel.setObjectName("surface")
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(22, 19, 22, 21)
    layout.setSpacing(12)
    return panel, layout


def _caption(text: str = "") -> QLabel:
    label = QLabel(text)
    label.setObjectName("pageHint")
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class Workspace(QWidget):
    """Unified window-native shell; no permanent sidebar, no scroll cutoff."""

    def __init__(self, namespace: str, locale: str = "vi", parent=None):
        super().__init__(parent)
        self.namespace = namespace
        self.locale = normalize_locale(locale)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        self.content = QWidget()
        scroll.setWidget(self.content)
        self.body = QVBoxLayout(self.content)
        self.body.setContentsMargins(32, 24, 32, 34)
        self.body.setSpacing(18)
        self.eyebrow = QLabel()
        self.eyebrow.setObjectName("eyebrow")
        self.body.addWidget(self.eyebrow)
        self.heading = QLabel()
        self.heading.setObjectName("heroTitle")
        self.heading.setWordWrap(True)
        self.body.addWidget(self.heading)
        self.intro = _caption()
        self.intro.setObjectName("heroCopy")
        self.body.addWidget(self.intro)

    def t(self, name: str, **fmt) -> str:
        return tr(self.locale, f"{self.namespace}.{name}", **fmt)

    def set_locale(self, locale: str):
        self.locale = normalize_locale(locale)
        self.eyebrow.setText(self.t("eyebrow"))
        self.heading.setText(self.t("title"))
        self.intro.setText(self.t("intro"))


class ObservationPlot(QWidget):
    """Small honest chart: no waveform and no synthetic series."""

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(238)
        self.points: list[RecordedPoint] = []
        self.accent = QColor("#48A6C8")

    def set_records(self, points: list[RecordedPoint]):
        self.points = sorted(points, key=lambda p: p.observed_at)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        painter.fillRect(self.rect(), palette.base())
        rect = self.rect().adjusted(46, 22, -21, -34)
        if rect.width() < 24 or rect.height() < 24:
            return
        muted = QColor(palette.text().color())
        muted.setAlpha(75)
        painter.setPen(QPen(muted, 1))
        for index in range(5):
            y = rect.top() + rect.height() * index / 4
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))
        if not self.points:
            return
        values = [p.value for p in self.points]
        ymin, ymax = min(values), max(values)
        if ymin == ymax:
            ymin -= max(1.0, abs(ymin) * .08)
            ymax += max(1.0, abs(ymax) * .08)
        else:
            pad = (ymax-ymin) * .09
            ymin -= pad
            ymax += pad
        times = [p.observed_at.timestamp() for p in self.points]
        tmin, tmax = min(times), max(times)
        if tmax <= tmin:
            tmin -= 60
            tmax += 60
        coords = [
            (rect.left() + rect.width() * (p.observed_at.timestamp()-tmin)/(tmax-tmin),
             rect.bottom() - rect.height() * (p.value-ymin)/(ymax-ymin))
            for p in self.points
        ]
        painter.setPen(QPen(muted, 1))
        painter.drawText(2, rect.top()+8, f"{ymax:g}")
        painter.drawText(2, rect.bottom(), f"{ymin:g}")
        if len(coords) >= 2 and len({p.source_id for p in self.points}) == 1:
            path = QPainterPath()
            path.moveTo(*coords[0])
            for point in coords[1:]:
                path.lineTo(*point)
            painter.setPen(QPen(self.accent, 2.6))
            painter.drawPath(path)
        painter.setPen(Qt.PenStyle.NoPen)
        for x, y in coords:
            painter.setBrush(self.accent)
            painter.drawEllipse(int(x)-4, int(y)-4, 8, 8)
        painter.setPen(QPen(muted, 1))
        painter.drawText(rect.left(), rect.bottom()+22, self.points[0].observed_at.strftime("%d/%m %H:%M"))
        painter.drawText(rect.right()-101, rect.bottom()+22, self.points[-1].observed_at.strftime("%d/%m %H:%M"))


class MonitoringWorkspace(Workspace):
    open_mission = Signal()

    def __init__(self, api_url: str, network, locale: str = "vi", parent=None):
        super().__init__("monitor", locale, parent)
        self.api_url = api_url.rstrip("/")
        self.network = network
        self.subject_id = ""
        self._token = ""
        self._request_seq = 0
        self.records: list[RecordedPoint] = []
        self.has_more = False
        header, controls = _panel()
        self.identity = _caption()
        controls.addWidget(self.identity)
        row = QHBoxLayout()
        self.link_mission = QPushButton()
        self.link_mission.clicked.connect(self.open_mission.emit)
        row.addWidget(self.link_mission)
        self.refresh_btn = QPushButton()
        self.refresh_btn.setObjectName("primaryAction")
        self.refresh_btn.clicked.connect(self.refresh)
        row.addWidget(self.refresh_btn)
        row.addStretch()
        controls.addLayout(row)
        self.status = _caption()
        controls.addWidget(self.status)
        self.body.addWidget(header)

        data, data_layout = _panel()
        filters = QHBoxLayout()
        self.metric_label = QLabel()
        filters.addWidget(self.metric_label)
        self.metric = QComboBox()
        self.metric.currentIndexChanged.connect(self._render)
        filters.addWidget(self.metric, 2)
        self.source_label = QLabel()
        filters.addWidget(self.source_label)
        self.source = QComboBox()
        self.source.currentIndexChanged.connect(self._render)
        filters.addWidget(self.source, 2)
        self.range_label = QLabel()
        filters.addWidget(self.range_label)
        self.period = QComboBox()
        self.period.addItem("24 h", 1)
        self.period.addItem("7 d", 7)
        self.period.addItem("All", 0)
        self.period.setCurrentIndex(2)
        self.period.currentIndexChanged.connect(self._render)
        filters.addWidget(self.period, 1)
        data_layout.addLayout(filters)
        self.plot = ObservationPlot()
        self.plot.setObjectName("monitorPlot")
        data_layout.addWidget(self.plot)
        self.plot_caption = _caption()
        data_layout.addWidget(self.plot_caption)
        self.body.addWidget(data)

        records, records_layout = _panel()
        self.records_title = QLabel()
        self.records_title.setObjectName("heading")
        records_layout.addWidget(self.records_title)
        self.table = QTableWidget(0, 8)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        for c, width in enumerate((145, 95, 85, 200, 185, 90, 120, 130)):
            self.table.setColumnWidth(c, width)
        self.table.setMinimumHeight(260)
        records_layout.addWidget(self.table)
        self.body.addWidget(records)

        ecg, ecg_layout = _panel()
        self.ecg_title = QLabel()
        self.ecg_title.setObjectName("heading")
        ecg_layout.addWidget(self.ecg_title)
        self.ecg_note = _caption()
        ecg_layout.addWidget(self.ecg_note)
        self.body.addWidget(ecg)
        self.body.addStretch()
        self.set_locale(locale)
        self._empty()

    def set_locale(self, locale: str):
        super().set_locale(locale)
        self.link_mission.setText(self.t("choose_subject"))
        self.refresh_btn.setText(self.t("refresh"))
        self.metric_label.setText(self.t("metric"))
        self.source_label.setText(self.t("source"))
        self.range_label.setText(self.t("range"))
        self.period.setItemText(0, self.t("day"))
        self.period.setItemText(1, self.t("week"))
        self.period.setItemText(2, self.t("all"))
        self.records_title.setText(self.t("records"))
        self.ecg_title.setText(self.t("ecg"))
        self.ecg_note.setText(self.t("no_waveform"))
        self.table.setHorizontalHeaderLabels([self.t(k) for k in
            ("col_metric", "col_value", "col_unit", "col_time", "col_source", "col_scope", "col_quality", "col_review")])
        self.identity.setText(self.t("selected", subject=self.subject_id) if self.subject_id else self.t("no_subject"))
        self._render()

    def _empty(self):
        self.records = []
        self.has_more = False
        self.metric.blockSignals(True)
        self.source.blockSignals(True)
        self.metric.clear()
        self.source.clear()
        self.metric.addItem(self.t("all_metrics"), None)
        self.source.addItem(self.t("all_sources"), None)
        self.metric.blockSignals(False)
        self.source.blockSignals(False)
        self.plot.set_records([])
        self.table.setRowCount(0)
        self.plot_caption.setText(self.t("no_data"))
        self.status.setText(self.t("no_data"))

    def select_subject(self, subject_id: str, access_token: str):
        self._request_seq += 1
        self._empty()
        self.subject_id = ""
        self._token = ""
        if not subject_id or len(subject_id) > 80 or not access_token:
            self.status.setText(self.t("denied"))
            return
        self.subject_id = subject_id
        self._token = access_token
        self.identity.setText(self.t("selected", subject=subject_id))
        self.refresh()

    def refresh(self):
        if not self.subject_id or not self._token:
            self._empty()
            self.status.setText(self.t("denied"))
            return
        self._request_seq += 1
        reqno = self._request_seq
        who = self.subject_id
        self._empty()
        self.status.setText(self.t("loading"))
        query = urlencode({"subject_id": who, "limit": 200})
        request = QNetworkRequest(QUrl(f"{self.api_url}/api/v1/observations?{query}"))
        request.setRawHeader(b"Authorization", ("Bearer " + self._token).encode("utf-8"))
        reply = self.network.get(request)
        reply.finished.connect(lambda: self._finished(reply, reqno, who))

    def _finished(self, reply, reqno: int, who: str):
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = reply.error() != QNetworkReply.NetworkError.NoError
        raw = bytes(reply.readAll())
        reply.deleteLater()
        if reqno != self._request_seq or who != self.subject_id:
            return
        if code in (401, 403):
            if code == 401:
                self._token = ""
            self.status.setText(self.t("denied"))
            return
        if code != 200 or error:
            self.status.setText(self.t("offline"))
            return
        try:
            rows, more = parse_recorded_observations(json.loads(raw.decode("utf-8")), who)
        except (ValueError, TypeError, UnicodeError, OverflowError):
            self.status.setText(self.t("invalid"))
            return
        self.records, self.has_more = rows, more
        self.metric.blockSignals(True)
        self.source.blockSignals(True)
        self.metric.clear()
        self.metric.addItem(self.t("all_metrics"), None)
        for metric, unit in sorted({(p.metric, p.unit) for p in rows}):
            self.metric.addItem(f"{metric} · {unit}", (metric, unit))
        self.source.clear()
        self.source.addItem(self.t("all_sources"), None)
        for name in sorted({p.source_id for p in rows}):
            self.source.addItem(name, name)
        self.metric.blockSignals(False)
        self.source.blockSignals(False)
        self.status.setText(self.t("loaded", count=len(rows)) + (" · "+self.t("more") if more else ""))
        self._render()

    def _render(self, *_):
        if not hasattr(self, "table"):
            return
        metric = self.metric.currentData()
        source = self.source.currentData()
        days = self.period.currentData()
        since = datetime.now(timezone.utc) - timedelta(days=days) if days else None
        filtered = [p for p in self.records
                    if (metric is None or (p.metric, p.unit) == metric)
                    and (source is None or p.source_id == source)
                    and (since is None or p.observed_at >= since)]
        self.table.setRowCount(len(filtered))
        for i, p in enumerate(filtered):
            data = (p.metric, f"{p.value:g}", p.unit, p.observed_at.isoformat(),
                    p.source_id, p.scope, p.quality, p.verification)
            for col, value in enumerate(data):
                self.table.setItem(i, col, QTableWidgetItem(str(value)))
        plotted = filtered if metric else []
        self.plot.set_records(plotted)
        if not filtered:
            self.plot_caption.setText(self.t("no_data"))
        elif metric is None:
            self.plot_caption.setText(self.t("select_metric"))
        elif len({p.source_id for p in plotted}) > 1:
            self.plot_caption.setText(self.t("multi_source"))
        else:
            self.plot_caption.setText(self.t("unverified_note"))


class InterviewWorkspace(Workspace):
    open_library = Signal()

    def __init__(self, api_url: str, network, locale="vi", parent=None):
        super().__init__("interview", locale, parent)
        self.api_url = api_url.rstrip("/")
        self.network = network
        self.request_seq = 0
        self.symptom = None
        self.answers: dict[str, str] = {}
        self.current_question = None
        self.ai_configured = False
        self.ai_provider = "disabled"
        search, search_layout = _panel()
        self.search_intro = _caption()
        search_layout.addWidget(self.search_intro)
        searchrow = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setMaxLength(120)
        self.search_edit.returnPressed.connect(self.search)
        searchrow.addWidget(self.search_edit, 1)
        self.search_btn = QPushButton()
        self.search_btn.setObjectName("primaryAction")
        self.search_btn.clicked.connect(self.search)
        searchrow.addWidget(self.search_btn)
        search_layout.addLayout(searchrow)
        self.results = QListWidget()
        self.results.setMaximumHeight(180)
        self.results.itemActivated.connect(self.choose)
        self.results.itemClicked.connect(self.choose)
        search_layout.addWidget(self.results)
        self.body.addWidget(search)

        interview, i_layout = _panel()
        self.mode_row = QHBoxLayout()
        self.ai_checkbox = QPushButton()
        self.ai_checkbox.setCheckable(True)
        self.ai_checkbox.setEnabled(False)
        self.ai_checkbox.clicked.connect(self._restart_request)
        self.mode_row.addWidget(self.ai_checkbox)
        self.cloud_checkbox = QPushButton()
        self.cloud_checkbox.setCheckable(True)
        self.cloud_checkbox.clicked.connect(self._restart_request)
        self.cloud_checkbox.hide()
        self.mode_row.addWidget(self.cloud_checkbox)
        self.model_label = _caption()
        self.mode_row.addWidget(self.model_label, 1)
        i_layout.addLayout(self.mode_row)
        self.selected = _caption()
        i_layout.addWidget(self.selected)
        self.question = QLabel()
        self.question.setObjectName("heading")
        self.question.setWordWrap(True)
        i_layout.addWidget(self.question)
        self.options_widget = QWidget()
        self.options = QHBoxLayout(self.options_widget)
        self.options.setContentsMargins(0, 4, 0, 4)
        self.options.setSpacing(9)
        i_layout.addWidget(self.options_widget)
        self.progress = _caption()
        i_layout.addWidget(self.progress)
        self.history = _caption()
        i_layout.addWidget(self.history)
        actionbar = QHBoxLayout()
        self.reset_btn = QPushButton()
        self.reset_btn.clicked.connect(self.reset)
        actionbar.addWidget(self.reset_btn)
        self.library_btn = QPushButton()
        self.library_btn.clicked.connect(self.open_library.emit)
        actionbar.addWidget(self.library_btn)
        actionbar.addStretch()
        i_layout.addLayout(actionbar)
        self.body.addWidget(interview)
        self.caution = _caption()
        self.body.addWidget(self.caution)
        self.body.addStretch()
        self.set_locale(locale)
        self.reset()
        self.check_ai_status()

    def set_locale(self, locale: str):
        super().set_locale(locale)
        self.search_intro.setText(self.t("search_help"))
        self.search_edit.setPlaceholderText(self.t("search_placeholder"))
        self.search_btn.setText(self.t("search"))
        self.ai_checkbox.setText(self.t("use_ai"))
        self.cloud_checkbox.setText(self.t("cloud_consent"))
        self.reset_btn.setText(self.t("reset"))
        self.library_btn.setText(self.t("library"))
        self.caution.setText(self.t("disclaimer"))
        self._render_question()

    def _request(self, path: str, method: str, body: dict | None, callback):
        self.request_seq += 1
        seq = self.request_seq
        req = QNetworkRequest(QUrl(self.api_url+path))
        if body is None:
            reply = self.network.get(req)
        else:
            req.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
            reply = self.network.post(req, json.dumps(body, ensure_ascii=False).encode("utf-8"))
        reply.finished.connect(lambda: callback(reply, seq))

    def check_ai_status(self):
        # Only admin/server decides which provider actually exists.
        def done(reply, seq):
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            raw = bytes(reply.readAll())
            reply.deleteLater()
            if code != 200:
                return
            try:
                status = json.loads(raw.decode("utf-8"))
                self.ai_configured = status.get("configured") is True
                self.ai_provider = str(status.get("provider", "disabled"))
                self.ai_checkbox.setEnabled(self.ai_configured)
                if not self.ai_configured:
                    self.ai_checkbox.setChecked(False)
                self.cloud_checkbox.setVisible(self.ai_configured and self.ai_provider == "openai")
                self._render_question()
            except (ValueError, UnicodeError, AttributeError):
                return
        self._request("/api/v1/knowledge/interview/ai-status", "GET", None, done)

    def search(self):
        phrase = self.search_edit.text().strip()
        if len(phrase) < 2:
            self.selected.setText(self.t("type_more"))
            return
        self.request_seq += 1
        seq = self.request_seq
        url = self.api_url+"/api/v1/knowledge/symptoms?"+urlencode({"query": phrase, "limit": 12})
        reply = self.network.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._searched(reply, seq))
        self.selected.setText(self.t("searching"))

    def _searched(self, reply, seq):
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw = bytes(reply.readAll())
        reply.deleteLater()
        if seq != self.request_seq:
            return
        self.results.clear()
        if code != 200:
            self.selected.setText(self.t("offline"))
            return
        try:
            payload = json.loads(raw.decode("utf-8"))
            items = payload.get("items", [])
            if not isinstance(items, list):
                raise ValueError("invalid result")
            for item in items:
                if not isinstance(item, dict):
                    continue
                name, ids = item.get("name"), item.get("ids")
                if not isinstance(name, str) or not isinstance(ids, list) or not ids:
                    continue
                choice = QListWidgetItem(name)
                choice.setData(Qt.ItemDataRole.UserRole, str(ids[0]))
                self.results.addItem(choice)
            self.selected.setText(self.t("result_count", count=self.results.count()))
        except (ValueError, UnicodeError, AttributeError):
            self.selected.setText(self.t("invalid"))

    def choose(self, item: QListWidgetItem):
        self.symptom = (item.text(), item.data(Qt.ItemDataRole.UserRole))
        self.answers.clear()
        self.results.clear()
        self.selected.setText(self.t("chosen", name=self.symptom[0]))
        self._ask_next()

    def _restart_request(self):
        if self.symptom:
            self._ask_next()

    def _ask_next(self):
        if not self.symptom:
            return
        body = {"symptoms": [self.symptom[1]], "answers": self.answers,
                "use_ai": self.ai_checkbox.isEnabled() and self.ai_checkbox.isChecked(),
                "allow_cloud": self.cloud_checkbox.isVisible() and self.cloud_checkbox.isChecked()}
        self.question.setText(self.t("loading"))
        self._request("/api/v1/knowledge/interview/next", "POST", body, self._asked)

    def _asked(self, reply, seq):
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw = bytes(reply.readAll())
        reply.deleteLater()
        if seq != self.request_seq:
            return
        if code != 200:
            self.question.setText(self.t("offline"))
            return
        try:
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict) or data.get("stored_by_server") is not False:
                raise ValueError("unrecognized interview response")
            next_question = data.get("next_question")
            if next_question is not None and (not isinstance(next_question, dict) or
                    not isinstance(next_question.get("id"), str) or
                    not isinstance(next_question.get("answers"), list)):
                raise ValueError("invalid next question")
            self.current_question = next_question
            self.last_response = data
            self._render_question()
        except (ValueError, TypeError, UnicodeError):
            self.question.setText(self.t("invalid"))

    def _clear_options(self):
        while self.options.count():
            item = self.options.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_question(self):
        if not hasattr(self, "question"):
            return
        self._clear_options()
        self.model_label.setText(self.t("model_state", status=self.ai_provider if self.ai_configured else self.t("no_model")))
        self.selected.setText(self.t("chosen", name=self.symptom[0]) if self.symptom else self.t("no_selection"))
        q = self.current_question
        if q is None:
            if self.symptom and hasattr(self, "last_response") and self.last_response.get("state") == "INTAKE_COMPLETED_UNVALIDATED":
                self.question.setText(self.t("completed"))
            else:
                self.question.setText(self.t("start"))
        else:
            self.question.setText(str(q.get("text", "")))
            for key in q.get("answers", []):
                if not isinstance(key, str) or len(key) > 24:
                    continue
                button = QPushButton(self.t("answer_"+key.lower()) if "answer_"+key.lower() in ANSWER_KEYS else key)
                button.setMinimumHeight(40)
                button.clicked.connect(lambda checked=False,k=key:self.answer(k))
                self.options.addWidget(button)
        if self.symptom and hasattr(self, "last_response"):
            result=self.last_response
            self.progress.setText(self.t("progress", count=result.get("answered",0), left=result.get("remaining",0)))
            history = result.get("session_history", [])
            self.history.setText(self.t("history", count=len(history)))
            if result.get("state") == "WITNESSED_RED_FLAG_REPORTED":
                self.progress.setText(self.t("urgent")+"\n"+self.progress.text())
        else:
            self.progress.setText(self.t("not_saved"))
            self.history.setText("")

    def answer(self, value: str):
        if not self.current_question or not self.symptom:
            return
        valid = self.current_question.get("answers", [])
        if value not in valid:
            return
        self.answers[self.current_question["id"]] = value
        self._ask_next()

    def reset(self):
        self.request_seq += 1
        self.symptom = None
        self.answers.clear()
        self.current_question = None
        if hasattr(self, "last_response"):
            del self.last_response
        self.results.clear()
        self._render_question()


ANSWER_KEYS = {"answer_yes", "answer_no", "answer_unknown", "answer_sudden",
               "answer_gradual", "answer_worse", "answer_same", "answer_better",
               "answer_measured", "answer_self_reported", "answer_minutes",
               "answer_hours", "answer_days", "answer_longer"}


class CareWorkspace(Workspace):
    open_personal = Signal()
    open_monitor = Signal()
    open_interview = Signal()

    def __init__(self, locale="vi", parent=None):
        super().__init__("care", locale, parent)
        self.active_step=0
        stagebar, stage_layout=_panel()
        self.steps=QHBoxLayout()
        self.step_buttons=[]
        for i in range(4):
            b=QPushButton()
            b.setCheckable(True)
            b.clicked.connect(lambda checked=False,j=i:self.select_step(j))
            self.steps.addWidget(b)
            self.step_buttons.append(b)
        stage_layout.addLayout(self.steps)
        self.body.addWidget(stagebar)
        stage, st_layout=_panel()
        self.stage_title=QLabel()
        self.stage_title.setObjectName("heading")
        st_layout.addWidget(self.stage_title)
        self.stage_detail=_caption()
        st_layout.addWidget(self.stage_detail)
        self.body.addWidget(stage)
        actions, act_layout=_panel()
        self.warning=_caption()
        act_layout.addWidget(self.warning)
        self.action_buttons=QHBoxLayout()
        self.open_intake=QPushButton()
        self.open_intake.setObjectName("primaryAction")
        self.open_intake.clicked.connect(self.open_interview.emit)
        self.action_buttons.addWidget(self.open_intake)
        self.open_measure=QPushButton()
        self.open_measure.clicked.connect(self.open_monitor.emit)
        self.action_buttons.addWidget(self.open_measure)
        self.open_health=QPushButton()
        self.open_health.clicked.connect(self.open_personal.emit)
        self.action_buttons.addWidget(self.open_health)
        act_layout.addLayout(self.action_buttons)
        self.body.addWidget(actions)
        self.body.addStretch()
        self.set_locale(locale)

    def set_locale(self, locale: str):
        super().set_locale(locale)
        self.open_intake.setText(self.t("start_interview"))
        self.open_measure.setText(self.t("open_monitor"))
        self.open_health.setText(self.t("open_health"))
        self.warning.setText(self.t("not_persistent"))
        for i, b in enumerate(self.step_buttons):
            b.setText(f"0{i+1} · "+self.t(f"step_{i}"))
        self.select_step(self.active_step)

    def select_step(self, index: int):
        self.active_step=index
        for j,b in enumerate(self.step_buttons):
            b.setChecked(j==index)
        self.stage_title.setText(self.t(f"step_{index}"))
        self.stage_detail.setText(self.t(f"detail_{index}"))
