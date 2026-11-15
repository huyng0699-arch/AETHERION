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
from html import escape
from urllib.parse import urlencode

from PySide6.QtCore import Qt, QUrl, Signal, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QToolTip,
    QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from .localization import normalize_locale, tr
from .monitoring_time import (TimeConductor, TimeBounds, TimeContext, visible_points,
                              segment_telemetry, utc_ticks, series_channel,
                              eligible_for_line, utc, format_utc_iso)


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
    """Native interactive time-series: UTC x-axis, honest source-separated lines.

    Unlike decorative sparklines, a data point is drawn ONLY from an authorized
    Server response. Unreviewed samples stay as markers; no hidden interpolation.
    """
    zoom_requested = Signal(float, float)   # factor and anchor fraction
    pan_requested = Signal(float)           # fraction of visible UTC span
    sample_selected = Signal(object)

    def __init__(self):
        super().__init__()
        self.setMinimumHeight(345)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setAccessibleName("UTC telemetry plot / time series")
        self.points = []
        self.edges = []
        self.bounds = TimeBounds(datetime.now(timezone.utc) - timedelta(days=7),
                                 datetime.now(timezone.utc) + timedelta(seconds=1))
        self.channel = None
        self.accent = QColor("#2F8BCB")
        self.chart_background = QColor("#FFFFFF")
        self.chart_text = QColor("#536C7D")
        self._pixel_points = []
        self._hover_point = None
        self._mouse_x = None
        self._drag_x = None
        self._gaps = 0
        self.empty_label = "Choose a measurement channel"

    def apply_palette(self, prefs):
        from .visual_theme import palette_for
        colors = palette_for(prefs.theme_name, prefs.mode,
                             prefs.high_contrast, prefs.accent_override)
        self.accent = QColor(colors.accent)
        self.chart_background = QColor(colors.surface)
        self.chart_text = QColor(colors.text)
        self.update()

    def set_series(self, points, bounds: TimeBounds, channel=None, source=None):
        self.bounds = bounds
        self.channel = channel
        self.points = visible_points(points, bounds, channel, source)
        _, self.edges, self._gaps = segment_telemetry(self.points, bounds, channel, source)
        self._hover_point = None
        self._pixel_points = []
        self.update()

    def set_records(self, points):  # compatibility for existing Qt integrations
        self.set_series(points, self.bounds, self.channel)

    def _chart_rect(self):
        return self.rect().adjusted(78, 62, -28, -65)

    def _source_color(self, source):
        hue = sum((i + 17) * ord(ch) for i, ch in enumerate(source)) % 360
        color = QColor.fromHsv(hue, 180, 208)
        if not color.isValid():
            color = QColor(self.accent)
        return color

    def _xy(self, point, rect, vmin, vmax):
        frac = (utc(point.observed_at) - self.bounds.start).total_seconds() / self.bounds.span.total_seconds()
        return (rect.left() + rect.width() * frac,
                rect.bottom() - rect.height() * (point.value - vmin) / (vmax - vmin))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.fillRect(self.rect(), self.chart_background)
        r = self._chart_rect()
        if r.width() < 70 or r.height() < 70:
            painter.end()
            return
        text = QColor(self.chart_text)
        grid = QColor(text)
        grid.setAlpha(43)
        sub = QColor(text)
        sub.setAlpha(190)
        painter.setPen(QPen(grid, 1))
        for i in range(5):
            yy = int(r.top() + r.height() * i / 4)
            painter.drawLine(r.left(), yy, r.right(), yy)
        for i, tick in enumerate(utc_ticks(self.bounds, 5)):
            xx = int(r.left() + r.width() * i / 4)
            painter.drawLine(xx, r.top(), xx, r.bottom())
            painter.setPen(QPen(sub, 1))
            label = tick.strftime("%d %b\n%H:%M")
            painter.drawText(xx - 37, r.bottom() + 15, 74, 38,
                             Qt.AlignmentFlag.AlignHCenter, label)
            painter.setPen(QPen(grid, 1))
        painter.setPen(QPen(text, 1))
        painter.drawText(r.left(), 20,
                         (" · ".join(self.channel) if self.channel else "TELEMETRY / UTC"))
        painter.drawText(r.left(), self.height() - 10, "UTC  •  observed_at")
        self._pixel_points = []
        if not self.points or self.channel is None:
            painter.setPen(QPen(sub, 1))
            painter.drawText(r, Qt.AlignmentFlag.AlignCenter, self.empty_label)
            painter.end()
            return
        values = [p.value for p in self.points]
        vmin, vmax = min(values), max(values)
        pad = max(0.01, abs(vmin) * .05, abs(vmax - vmin) * .09)
        vmin -= pad
        vmax += pad
        if vmax <= vmin:
            vmax = vmin + 1
        painter.setPen(QPen(sub, 1))
        painter.drawText(8, r.top() + 6, f"{vmax:.4g}")
        painter.drawText(8, r.bottom(), f"{vmin:.4g}")
        painter.drawText(8, r.center().y(), self.channel[1])
        coords = [(p, self._xy(p, r, vmin, vmax)) for p in self.points]
        mapping = {id(p): xy for p, xy in coords}
        painter.save()
        painter.setClipRect(r)
        for left, right in self.edges:
            xy1 = mapping.get(id(left))
            xy2 = mapping.get(id(right))
            if not xy1 or not xy2:
                continue
            painter.setPen(QPen(self._source_color(left.source_id), 2.1))
            painter.drawLine(QPointF(*xy1), QPointF(*xy2))
        for p, (x, y) in coords:
            c = self._source_color(p.source_id)
            painter.setPen(QPen(c, 1.8))
            if eligible_for_line(p):
                painter.setBrush(c)
            else:
                painter.setBrush(self.chart_background)  # unverified = outlined sample
            painter.drawEllipse(QPointF(x, y), 3.8, 3.8)
            self._pixel_points.append((p, x, y))
        if self._hover_point is not None:
            pt = next(((x, y) for p, x, y in self._pixel_points if p is self._hover_point), None)
            if pt:
                x, y = pt
                pen = QPen(sub, 1)
                pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawLine(QPointF(x, r.top()), QPointF(x, r.bottom()))
                painter.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
                painter.setPen(QPen(self.accent, 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QPointF(x, y), 7.5, 7.5)
        painter.restore()
        painter.end()

    def _nearest(self, pos):
        if not self._chart_rect().contains(pos.toPoint()):
            return None
        best, score = None, 144.0
        for p, x, y in self._pixel_points:
            d = (x - pos.x()) ** 2 + (y - pos.y()) ** 2
            if d < score:
                best, score = p, d
        return best

    def mouseMoveEvent(self, event):
        if self._drag_x is not None:
            self._mouse_x = event.position().x()
            return
        point = self._nearest(event.position())
        if point is not self._hover_point:
            self._hover_point = point
            if point:
                stamp = utc(point.observed_at).strftime("%Y-%m-%d %H:%M:%S UTC")
                QToolTip.showText(event.globalPosition().toPoint(),
                    f"{stamp}\n{point.metric}: {point.value:g} {point.unit}\n"
                    f"{point.source_id} / {point.scope}\n"
                    f"{point.quality} / {point.verification}", self)
            else:
                QToolTip.hideText()
            self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hover_point = None
        self._drag_x = None
        QToolTip.hideText()
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._chart_rect().contains(event.position().toPoint()):
            self._drag_x = event.position().x()
            self._mouse_x = self._drag_x
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._drag_x is not None:
            delta = event.position().x() - self._drag_x
            self._drag_x = None
            self._mouse_x = None
            self.setCursor(Qt.CursorShape.CrossCursor)
            if abs(delta) > 6 and self._chart_rect().width() > 0:
                self.pan_requested.emit(-delta / self._chart_rect().width())
            else:
                p = self._nearest(event.position())
                if p is not None:
                    self.sample_selected.emit(p)
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        if self._chart_rect().contains(event.position().toPoint()):
            factor = .75 if event.angleDelta().y() > 0 else 1.333333
            anchor = (event.position().x() - self._chart_rect().left()) / max(1, self._chart_rect().width())
            self.zoom_requested.emit(factor, min(1., max(0., anchor)))
            event.accept()
        else:
            super().wheelEvent(event)


_MONITOR_TEXT = {
    "vi": {
        "time_title": "BỘ ĐIỀU KHIỂN THỜI GIAN • UTC", "latest": "Mới nhất · làm mới 60 giây", "fixed": "Khoảng cố định", "utc_since": "Từ UTC", "utc_until": "Đến UTC", "apply": "Áp dụng", "day30": "30 ngày", "zoom_in": "Phóng to +", "zoom_out": "Thu nhỏ −", "pan_left": "← Trước", "pan_right": "Sau →", "all_scope": "Mọi phạm vi", "channel": "Kênh / chỉ số", "legend": "CHÚ GIẢI NGUỒN & CHẤT LƯỢNG", "gap": "khoảng trống", "scatter": "Điểm chưa thẩm định = vòng rỗng; chỉ nối READY + VERIFIED cùng nguồn khi có đủ nhịp lấy mẫu.", "loaded_window": "{count} điểm / {sources} nguồn / {gaps} khoảng trống; cửa sổ UTC {start} → {end}", "partial": "Một phần dữ liệu: đạt giới hạn phân trang {limit} điểm. Hãy chọn kênh hoặc cửa sổ ngắn hơn.", "bad_utc": "Ngày phải nhập dạng YYYY-MM-DD HH:MM:SS UTC; khoảng 1 phút–366 ngày.", "no_rows": "Không có bản ghi trong cửa sổ UTC được chọn.", "available": "Kênh hiện có trên Server", "inspect": "Di chuột qua điểm để xem nguồn • nhấn để chọn bản ghi • kéo ngang để pan • cuộn để zoom", "no_link": "Không nối dữ liệu qua khoảng trống hay giữa nguồn/chất lượng khác nhau.", "unknown_cadence": "Không đủ mẫu để xác định nhịp lấy mẫu; hiển thị điểm riêng lẻ.", "fixed_utc": "UTC cố định", "source_quality": "{source} · {quality} · {count} điểm", "window_busy": "Đang truy xuất dữ liệu theo khoảng UTC, có xác thực…", "verified": "Đã xác minh", "unverified": "Chưa xác minh", "invalid_page": "ERROR · Trang dữ liệu thiếu cursor/metadata hoặc khác chủ thể; đã từ chối toàn bộ.", "page_limit": "Giới hạn tối đa 2.500 điểm mỗi cửa sổ; lọc kênh hoặc rút thời gian.", "points": "điểm", "data_gap": "Khoảng trống và mẫu chưa xác minh không được nội suy.", "no_channel": "Chọn kênh có cùng phạm vi và đơn vị để xem biểu đồ."},
    "en": {
        "time_title": "SHARED TIME CONDUCTOR • UTC", "latest": "Latest · 60-second refresh", "fixed": "Fixed time window", "utc_since": "From UTC", "utc_until": "To UTC", "apply": "Apply", "day30": "30 days", "zoom_in": "Zoom in +", "zoom_out": "Zoom out −", "pan_left": "← Earlier", "pan_right": "Later →", "all_scope": "All scopes", "channel": "Channel / metric", "legend": "SOURCE & QUALITY LEGEND", "gap": "gaps", "scatter": "Unreviewed = hollow marker; join only READY + VERIFIED samples from one source with inferable cadence.", "loaded_window": "{count} samples / {sources} sources / {gaps} gaps; UTC window {start} → {end}", "partial": "Partial query: {limit}-point pagination cap reached. Select a channel or shorter UTC window.", "bad_utc": "Enter YYYY-MM-DD HH:MM:SS UTC; bounds must span 1 minute–366 days.", "no_rows": "No observations for this selected UTC window.", "available": "Channels available from Server", "inspect": "Hover for provenance • click a marker for its row • drag horizontally to pan • wheel to zoom", "no_link": "Never join across source/quality changes or missing time spans.", "unknown_cadence": "Sample cadence cannot be inferred; points displayed separately.", "fixed_utc": "Fixed UTC", "source_quality": "{source} · {quality} · {count} points", "window_busy": "Loading authorized UTC-bounded records…", "verified": "Verified", "unverified": "Unverified", "invalid_page": "ERROR · Missing page cursor/metadata or mismatched subject; entire response rejected.", "page_limit": "Maximum 2,500 points/window; filter channel or narrow time.", "points": "samples", "data_gap": "Missing and unreviewed signals are never interpolated.", "no_channel": "Choose one channel with a consistent scope and unit."}
}


class MonitoringWorkspace(Workspace):
    """UTC-scoped channel explorer backed by the authenticated observation API.

    Time conductor is ONE source of truth for plot + table + HTTP queries. The
    Server's cursor is respected, and partial windows are disclosed, not drawn
    as complete histories. No changes to shared app or i18n files.
    """
    open_mission = Signal()
    # mode, start_utc, end_utc; timestamps are offset-aware UTC ISO strings.
    time_context_changed = Signal(str, str, str)
    PAGE_LIMIT = 500
    MAX_PAGES = 5

    def __init__(self, api_url: str, network, locale="vi", parent=None):
        super().__init__("monitor", locale, parent)
        self.api_url = api_url.rstrip("/")
        self.network = network
        self.subject_id = ""
        self._token = ""
        self._request_seq = 0
        self.records = []
        self.has_more = False
        self._cursor_seen = set()
        self._page_count = 0
        self._partial = False
        self._discovered_channels = set()
        self._desired_source = None
        self.conductor = TimeConductor(timedelta(days=7))
        self._active_metric = None
        self._loaded_rows = []

        top, top_layout = _panel()
        self.identity = _caption()
        top_layout.addWidget(self.identity)
        controls = QHBoxLayout()
        self.link_mission = QPushButton()
        self.link_mission.clicked.connect(self.open_mission.emit)
        controls.addWidget(self.link_mission)
        self.refresh_btn = QPushButton()
        self.refresh_btn.setObjectName("primaryAction")
        self.refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(self.refresh_btn)
        controls.addStretch()
        top_layout.addLayout(controls)
        self.status = _caption()
        top_layout.addWidget(self.status)
        self.body.addWidget(top)

        conductor_panel, conductor_layout = _panel()
        self.time_title = QLabel()
        self.time_title.setObjectName("heading")
        conductor_layout.addWidget(self.time_title)
        self.mode_row = QHBoxLayout()
        self.mode = QComboBox()
        self.mode.addItem("Latest", "latest")
        self.mode.addItem("Fixed", "fixed")
        self.mode.currentIndexChanged.connect(self._on_mode)
        self.mode_row.addWidget(self.mode, 1)
        self.preset = []
        for days in (1, 7, 30):
            button = QPushButton()
            button.setObjectName("navButton")
            button.clicked.connect(lambda checked=False, d=days: self._preset(d))
            self.mode_row.addWidget(button)
            self.preset.append(button)
        self.mode_row.addStretch()
        conductor_layout.addLayout(self.mode_row)
        interval = QHBoxLayout()
        self.start_label = QLabel()
        interval.addWidget(self.start_label)
        self.start_edit = QLineEdit()
        self.start_edit.setInputMask("0000-00-00 00:00:00;_")
        self.start_edit.setMaximumWidth(208)
        self.start_edit.setAccessibleName("UTC start bound")
        interval.addWidget(self.start_edit)
        self.end_label = QLabel()
        interval.addWidget(self.end_label)
        self.end_edit = QLineEdit()
        self.end_edit.setInputMask("0000-00-00 00:00:00;_")
        self.end_edit.setMaximumWidth(208)
        self.end_edit.setAccessibleName("UTC end bound")
        interval.addWidget(self.end_edit)
        self.apply_btn = QPushButton()
        self.apply_btn.clicked.connect(self._apply_bounds)
        interval.addWidget(self.apply_btn)
        conductor_layout.addLayout(interval)
        toolbar = QHBoxLayout()
        self.zoom_in = QPushButton()
        self.zoom_in.clicked.connect(lambda: self._zoom(.6, .5))
        toolbar.addWidget(self.zoom_in)
        self.zoom_out = QPushButton()
        self.zoom_out.clicked.connect(lambda: self._zoom(1.667, .5))
        toolbar.addWidget(self.zoom_out)
        self.pan_left = QPushButton()
        self.pan_left.clicked.connect(lambda: self._pan(-.5))
        toolbar.addWidget(self.pan_left)
        self.pan_right = QPushButton()
        self.pan_right.clicked.connect(lambda: self._pan(.5))
        toolbar.addWidget(self.pan_right)
        toolbar.addStretch()
        conductor_layout.addLayout(toolbar)
        self.body.addWidget(conductor_panel)

        panel, content = _panel()
        selectors = QHBoxLayout()
        self.metric_label = QLabel()
        selectors.addWidget(self.metric_label)
        self.metric_box = QComboBox()  # never shadow QWidget.metric()
        self.metric_box.setMinimumWidth(170)
        self.metric_box.setAccessibleName("Telemetry channel")
        self.metric_box.currentIndexChanged.connect(self._channel_changed)
        selectors.addWidget(self.metric_box, 3)
        self.source_label = QLabel()
        selectors.addWidget(self.source_label)
        self.source = QComboBox()
        self.source.setMinimumWidth(110)
        self.source.currentIndexChanged.connect(self._source_changed)
        selectors.addWidget(self.source, 2)
        content.addLayout(selectors)
        self.plot = ObservationPlot()
        self.plot.setObjectName("monitorPlot")
        self.plot.zoom_requested.connect(self._zoom)
        self.plot.pan_requested.connect(self._pan)
        self.plot.sample_selected.connect(self._select_sample)
        content.addWidget(self.plot, 2)
        self.legend_title = QLabel()
        self.legend_title.setObjectName("heading")
        content.addWidget(self.legend_title)
        self.legend = _caption()
        self.legend.setTextFormat(Qt.TextFormat.RichText)
        content.addWidget(self.legend)
        self.plot_caption = _caption()
        content.addWidget(self.plot_caption)
        self.body.addWidget(panel)

        table_panel, table_layout = _panel()
        self.records_title = QLabel()
        self.records_title.setObjectName("heading")
        table_layout.addWidget(self.records_title)
        self.table = QTableWidget(0, 8)
        self.table.setObjectName("monitorTelemetryTable")
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSortingEnabled(True)
        self.table.setMinimumHeight(300)
        for i, w in enumerate((145, 105, 80, 200, 165, 90, 110, 115)):
            self.table.setColumnWidth(i, w)
        table_layout.addWidget(self.table)
        self.body.addWidget(table_panel)

        self.ecg_title = QLabel()
        self.ecg_note = _caption()
        ecg_panel, ecg_layout = _panel()
        ecg_layout.addWidget(self.ecg_title)
        ecg_layout.addWidget(self.ecg_note)
        self.body.addWidget(ecg_panel)
        self.body.addStretch()
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(60000)  # polling, NOT a subscribed telemetry stream
        self.poll_timer.timeout.connect(self._poll_latest)
        self.poll_timer.start()
        self.set_locale(locale)
        self._empty(clear_channels=True)

    def tx(self, key, **params):
        text = _MONITOR_TEXT[self.locale].get(key, key)
        return text.format(**params) if params else text

    def apply_theme(self, prefs):
        self.plot.apply_palette(prefs)

    def set_locale(self, locale: str):
        super().set_locale(locale)
        self.link_mission.setText(self.t("choose_subject"))
        self.refresh_btn.setText(self.t("refresh"))
        self.time_title.setText(self.tx("time_title"))
        self.mode.setItemText(0, self.tx("latest"))
        self.mode.setItemText(1, self.tx("fixed"))
        for button, key in zip(self.preset, ("day", "week", "day30")):
            button.setText(self.t(key) if key in ("day", "week") else self.tx(key))
        self.start_label.setText(self.tx("utc_since"))
        self.end_label.setText(self.tx("utc_until"))
        self.apply_btn.setText(self.tx("apply"))
        self.zoom_in.setText(self.tx("zoom_in"))
        self.zoom_out.setText(self.tx("zoom_out"))
        self.pan_left.setText(self.tx("pan_left"))
        self.pan_right.setText(self.tx("pan_right"))
        self.metric_label.setText(self.tx("channel"))
        self.source_label.setText(self.t("source"))
        self.legend_title.setText(self.tx("legend"))
        self.records_title.setText(self.t("records"))
        self.ecg_title.setText(self.t("ecg"))
        self.ecg_note.setText(self.t("no_waveform"))
        self.plot.empty_label = self.tx("no_channel")
        self.table.setHorizontalHeaderLabels([self.t(k) for k in
            ("col_metric", "col_value", "col_unit", "col_time", "col_source", "col_scope", "col_quality", "col_review")])
        self.identity.setText(self.t("selected", subject=self.subject_id) if self.subject_id else self.t("no_subject"))
        if self.metric_box.count(): self.metric_box.setItemText(0, self.t("all_metrics"))
        if self.source.count(): self.source.setItemText(0, self.t("all_sources"))
        self._update_bounds_edits()
        self._render()

    def _update_bounds_edits(self):
        for edit, value in ((self.start_edit, self.conductor.bounds.start),
                            (self.end_edit, self.conductor.bounds.end)):
            edit.setText(value.strftime("%Y-%m-%d %H:%M:%S"))
        self.mode.blockSignals(True)
        self.mode.setCurrentIndex(0 if self.conductor.mode == "latest" else 1)
        self.mode.blockSignals(False)

    def _empty(self, clear_channels=False):
        self.records.clear()
        self.has_more = False
        self._page_count = 0
        self._cursor_seen = set()
        self._partial = False
        self._loaded_rows = []
        if clear_channels:
            self._desired_source = None
            self._discovered_channels = set()
            self.metric_box.blockSignals(True)
            self.metric_box.clear()
            self.metric_box.addItem(self.t("all_metrics"), None)
            self.metric_box.blockSignals(False)
        self.source.blockSignals(True)
        self.source.clear()
        self.source.addItem(self.t("all_sources"), None)
        self.source.blockSignals(False)
        self.table.setRowCount(0)
        self.plot.set_series([], self.conductor.bounds)
        self.legend.setText(self.tx("no_rows"))
        self.plot_caption.setText(self.tx("no_rows"))

    def select_subject(self, subject_id: str, access_token: str):
        self._request_seq += 1
        self._empty(clear_channels=True)
        self._token = ""
        self.subject_id = ""
        if not subject_id or len(subject_id) > 80 or not access_token:
            self.identity.setText(self.t("no_subject"))
            self.status.setText(self.t("denied"))
            return
        self.subject_id = subject_id
        self._token = access_token
        self.identity.setText(self.t("selected", subject=subject_id))
        self.refresh()

    def current_time_context(self) -> TimeContext:
        """Return the exact mode and UTC bounds used by query, plot and table."""
        return self.conductor.snapshot()

    def _emit_time_context_changed(self):
        context = self.current_time_context()
        self.time_context_changed.emit(context.mode, context.start_utc, context.end_utc)

    def _finish_local_time_change(self, previous: TimeContext):
        self._update_bounds_edits()
        self.refresh(advance_latest=False, publish_time_context=False)
        if self.current_time_context() != previous:
            self._emit_time_context_changed()

    def set_external_utc_bounds(self, start_utc: str, end_utc: str, *,
                                mode: str = "fixed") -> bool:
        """Apply a host time context without changing auth or data filters.

        Input must be offset-aware ISO-8601; mode is latest or fixed.
        Invalid mode, timestamps or span raise ValueError. Returns False without
        changing state unless Monitoring already has an authorized subject token.
        The existing metric/channel and local source filter are preserved.
        Applying host state never echoes the signal, so shell synchronization
        cannot recurse. Authenticated HTTP remains the only record source.
        """
        context = TimeContext.from_iso(mode, start_utc, end_utc)
        if not self.subject_id or not self._token:
            return False
        self.conductor.set_context(context)
        self._update_bounds_edits()
        self.refresh(advance_latest=False, publish_time_context=False)
        return True

    def _preset(self, days):
        previous = self.current_time_context()
        self.conductor.latest(timedelta(days=days))
        self._finish_local_time_change(previous)

    def _on_mode(self, *_):
        previous = self.current_time_context()
        if self.mode.currentData() == "latest":
            self.conductor.latest()
        else:
            self.conductor.fixed(self.conductor.bounds.start, self.conductor.bounds.end)
        self._finish_local_time_change(previous)

    def _apply_bounds(self):
        previous = self.current_time_context()
        try:
            start = datetime.strptime(self.start_edit.text(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            end = datetime.strptime(self.end_edit.text(), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            self.conductor.fixed(start, end)
        except ValueError:
            self.status.setText(self.tx("bad_utc"))
            self._update_bounds_edits()
            return
        self._finish_local_time_change(previous)

    def sync_utc_window(self, start_iso: str, end_iso: str):
        """Legacy Home adapter; naive strings retain their historical UTC meaning."""
        if not self.subject_id or not self._token:
            return False
        try:
            def legacy_utc(value):
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                if parsed.tzinfo is None or parsed.utcoffset() is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return format_utc_iso(parsed)
            return self.set_external_utc_bounds(
                legacy_utc(start_iso), legacy_utc(end_iso), mode="fixed")
        except (TypeError, ValueError):
            return False

    def _zoom(self, factor: float, anchor: float):
        previous = self.current_time_context()
        try:
            self.conductor.zoom(factor, anchor)
        except ValueError:
            return
        self._finish_local_time_change(previous)

    def _pan(self, fraction: float):
        previous = self.current_time_context()
        try:
            self.conductor.pan(fraction)
        except ValueError:
            return
        self._finish_local_time_change(previous)

    def _poll_latest(self):
        if self.conductor.mode == "latest" and self.isVisible() and self._token:
            self.refresh()

    def _channel_changed(self, *_):
        self._active_metric = self.metric_box.currentData()
        self.refresh()

    def _source_changed(self, *_):
        self._desired_source = self.source.currentData()
        self._render()

    def refresh(self, *_qt_args, advance_latest=True, publish_time_context=True):
        previous = self.current_time_context()
        if advance_latest and self.conductor.mode == "latest":
            self.conductor.latest()
        self._update_bounds_edits()
        if publish_time_context and self.current_time_context() != previous:
            self._emit_time_context_changed()
        if not self.subject_id or not self._token:
            self._request_seq += 1
            self._empty(clear_channels=True)
            self.status.setText(self.t("denied"))
            return
        self._request_seq += 1
        self._empty(clear_channels=False)
        self.status.setText(self.tx("window_busy"))
        self._request_page(self._request_seq, cursor=None)

    def _request_page(self, reqno, cursor):
        if reqno != self._request_seq:
            return
        args = {"subject_id": self.subject_id, "limit": self.PAGE_LIMIT,
                "order": "asc", **self.conductor.bounds.as_query()}
        channel = self.metric_box.currentData()
        if channel is not None:
            args["metric"] = channel[0]
            args["scope"] = channel[2]
        if cursor:
            args["cursor"] = cursor
        url = f"{self.api_url}/api/v1/observations?{urlencode(args)}"
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader(b"Authorization", ("Bearer " + self._token).encode("utf-8"))
        reply = self.network.get(req)
        reply.finished.connect(lambda: self._finished(reply, reqno))

    def _finished(self, reply, reqno):
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        network_error = reply.error() != QNetworkReply.NetworkError.NoError
        raw = bytes(reply.readAll())
        reply.deleteLater()
        if reqno != self._request_seq:
            return
        if code in (401, 403):
            self._token = ""
            self._empty(clear_channels=True)
            self.status.setText(self.t("denied"))
            return
        if code != 200 or network_error:
            self._empty(clear_channels=True)
            self.status.setText(self.t("offline"))
            return
        try:
            payload = json.loads(raw.decode("utf-8"))
            page, more = parse_recorded_observations(payload, self.subject_id)
            cursor = payload.get("next_cursor")
            if payload.get("order") != "asc":
                raise ValueError("wrong page order")
            if more and (not isinstance(cursor, str) or len(cursor) > 200 or cursor in self._cursor_seen):
                raise ValueError("missing / repeating cursor")
            if any(not self.conductor.bounds.contains(p.observed_at) for p in page):
                raise ValueError("out-of-window page")
            self.records.extend(page)
            self._page_count += 1
            if more:
                self._cursor_seen.add(cursor)
                if self._page_count < self.MAX_PAGES:
                    self._request_page(reqno, cursor)
                    return
                self._partial = True
            self.has_more = more
            self._populate_filters()
            self._render()
            count = len(self.records)
            text = self.t("loaded", count=count)
            if self._partial:
                text += " · " + self.tx("partial", limit=self.MAX_PAGES * self.PAGE_LIMIT)
            self.status.setText(text)
        except (ValueError, TypeError, UnicodeError, OverflowError, AttributeError):
            self._request_seq += 1
            self._empty(clear_channels=True)
            self.status.setText(self.tx("invalid_page"))

    def _populate_filters(self):
        current = self.metric_box.currentData()
        self._discovered_channels.update(series_channel(p) for p in self.records)
        self.metric_box.blockSignals(True)
        self.metric_box.clear()
        self.metric_box.addItem(self.t("all_metrics"), None)
        for channel in sorted(self._discovered_channels):
            self.metric_box.addItem(" / ".join(channel), channel)
        index = self.metric_box.findData(current)
        self.metric_box.setCurrentIndex(max(index, 0))
        self.metric_box.blockSignals(False)
        chosen_source = self._desired_source
        self.source.blockSignals(True)
        self.source.clear()
        self.source.addItem(self.t("all_sources"), None)
        for name in sorted({p.source_id for p in self.records}):
            self.source.addItem(name, name)
        index = self.source.findData(chosen_source)
        self.source.setCurrentIndex(max(index, 0))
        self.source.blockSignals(False)

    def _render(self, *_):
        if not hasattr(self, "table") or not hasattr(self, "metric_box"):
            return
        channel = self.metric_box.currentData()
        source = self.source.currentData()
        filtered = visible_points(self.records, self.conductor.bounds, channel, source)
        self.plot.set_series(filtered, self.conductor.bounds, channel, source)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(filtered))
        self._loaded_rows = list(filtered)
        for i, p in enumerate(filtered):
            data = (p.metric, f"{p.value:g}", p.unit,
                    utc(p.observed_at).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    p.source_id, p.scope, p.quality, p.verification)
            for j, item in enumerate(data):
                widget = QTableWidgetItem(str(item))
                if j in (1, 3): widget.setData(Qt.ItemDataRole.UserRole, p)
                self.table.setItem(i, j, widget)
        self.table.setSortingEnabled(True)
        groups, edges, gaps = segment_telemetry(filtered, self.conductor.bounds, channel, source)
        line = []
        for (source_id, scope, metric, unit), samples in sorted(groups.items()):
            quals = sorted(set(p.quality + "/" + p.verification for p in samples))
            color = self.plot._source_color(source_id).name()
            legend_label = self.tx("source_quality", source=source_id,
                                   quality=", ".join(quals), count=len(samples))
            line.append(f'<span style="color:{color};font-weight:800">◆</span> '
                        f'{escape(legend_label)}')
        self.legend.setText(" &nbsp;&nbsp; • &nbsp;&nbsp; ".join(line) if line
                            else escape(self.tx("no_rows")))
        count = len(filtered)
        if not count:
            self.plot_caption.setText(self.tx("no_rows"))
        elif channel is None:
            self.plot_caption.setText(self.tx("no_channel"))
        else:
            self.plot_caption.setText(
                self.tx("loaded_window", count=count, sources=len(groups), gaps=gaps,
                        start=self.conductor.bounds.start.strftime("%Y-%m-%d %H:%M"),
                        end=self.conductor.bounds.end.strftime("%Y-%m-%d %H:%M"))
                + "\n" + self.tx("inspect") + "\n" + self.tx("scatter"))

    def _select_sample(self, p):
        # After QTableWidget sorting, locate by stored object identity, not row index.
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item and item.data(Qt.ItemDataRole.UserRole) is p:
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                break



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
        self.steps = QGridLayout()
        self.steps.setSpacing(8)
        self.step_buttons = []
        for i in range(4):
            b = QPushButton()
            b.setCheckable(True)
            b.setMinimumWidth(0)
            b.clicked.connect(lambda checked=False, j=i: self.select_step(j))
            self.steps.addWidget(b, i // 2, i % 2)
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
