"""AETHERION native Mission Operations Home (Q-0485).

Functional Browse / Workspace / Inspect / shared UTC Time Conductor, designed
for the actual native Windows client. No decorative orbit or invented sensors.

Historical NASA Mercury-Atlas 7 values are source-backed, not synthetic and
usually lack a precise absolute UTC observation timestamp. They are shown in
original report order, *never* silently assigned fabricated UTC instants.

The real-time UTC workspace starts empty: a trusted, authorization-preserving
host may supply previously validated non-synthetic UTC observations through
set_verified_observations(). There is no automatic unscoped server query here.

Public integration API kept stable for AetherionWindow:
 build_mission_ops_home(parent=None, locale=..., reduce_motion=...)
 route_requested(str), simulated_demo_requested(), nasa_archive_requested()
 set_locale(locale), set_visuals(theme, reduce_motion, mode, intensity)
 set_connection_state(string)
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
import re
from urllib.parse import urlsplit

from PySide6.QtCore import Qt, QDateTime, QRectF, QTimeZone, Signal, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateTimeEdit, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QListWidget, QPushButton, QSplitter, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from .visual_theme import palette_for
from .monitoring_time import MAX_SPAN, MIN_SPAN
from .features.demo.nasa_ma7 import load_real_nasa_data

ROUTE_IDS = (
    "mission", "health", "monitor", "ecg", "assistant", "interview",
    "care", "care_guide", "science", "hazards", "medical_library", "atlas",
    "crew", "settings",
)

# These are the only source groups that can be displayed as original NASA data.
SOURCE_GROUPS = ("flight", "clinical", "blood", "pressure")

TEXT = {
    "en": {
        "brand": "AETHERION  /  MISSION OPERATIONS",
        "connection": "Unverified connection",
        "browse": "BROWSE",
        "browseSearch": "Search objects and routes…",
        "utcMetricFilter": "Filter UTC records by metric and unit",
        "utcSourceFilter": "Filter UTC records by verified source",
        "utcAllMetrics": "All metric families",
        "utcAllSources": "All verified sources",
        "utcChartSeries": "One selected metric and unit · one selected source · verification stays in Inspect · discrete samples only · no interpolation",
        "utcChartNeedsFilter": "Choose one metric/unit and one source to display a single series. Verification remains in Inspect.",
        "utcXAxis": "TIME · UTC",
        "utcYAxis": "VALUE · {unit}",
        "utcSeriesTitle": "SELECTED SERIES · {metric} ({unit}) · {source}",

        "inspect": "INSPECT  /  PROPERTIES",
        "workspace": "WORKSPACE",
        "science": "SCIENCE & SOURCES",
        "clinical": "HEALTH & CARE",
        "systems": "SYSTEMS",
        "mission": "Mission",
        "crew": "Crew",
        "health": "My Health",
        "monitor": "Monitoring",
        "ecg": "ECG",
        "assistant": "Ask AI",
        "interview": "Symptom Interview",
        "care": "Care Journey",
        "care_guide": "Care Guide",
        "science_route": "Scientific Observatory",
        "hazards": "NASA Hazards",
        "medical_library": "Medical Library",
        "atlas": "Body Atlas",
        "settings": "Settings",
        "home": "Mission Workspace",
        "archive": "NASA MA-7 · source records",
        "utc": "UTC observations",
        "demo": "SIMULATED DEMO",
        "sim": "SIMULATED",
        "real": "NASA MA-7 · 1962",
        "realBadge": "HISTORICAL · NASA SOURCE",
        "simulationHint": "Fictional five-patient scenario, stored separately from actual health records",
        "archiveHint": "83 published measurements across 19 archived report timepoints",
        "runDemo": "Explore SIMULATED Demo",
        "runArchive": "Open NASA archive",
        "sourceGuide": "Open NASA original report",
        "launch": "Open feature",
        "welcome": "Select a source or work area in Browse.",
        "welcomeLead": "The workspace shows authentic historical NASA measurements and honest empty states for unconnected UTC observations. No fabricated live telemetry.",
        "welcomeSource": "Source inventory",
        "welcomeCount": "{records} original MA-7 report timepoints · {values} recorded values",
        "welcomeNoSource": "The NASA source package is unavailable or invalid. Open the archive for details.",
        "welcomeReal": "Read the NASA MA-7 records",
        "welcomeUtc": "Inspect UTC records",
        "homeNotice": "The mission workspace does not read authenticated patients until a permitted source supplies them.",
        "time": "TIME CONDUCTOR",
        "timeHelp": "UTC window shared by UTC plot, table, and Inspect",
        "from": "From",
        "to": "To",
        "recentDay": "24 h",
        "recentWeek": "7 d",
        "recentMonth": "30 d",
        "apply": "Apply UTC range",
        "timeInvalid": "Invalid UTC interval: Start must be earlier than End.",
        "timeRangeTooShort": "UTC range must be at least 1 minute.",
        "timeRangeTooLong": "UTC range cannot exceed 366 days.",
        "timeWindow": "UTC window: {start} — {end}",
        "timeSource": "NASA MA-7 original timepoints do not have verifiable absolute UTC timestamps. UTC bounds are not applied to this historical archive.",
        "sourceTitle": "Mercury-Atlas 7 · original recorded values",
        "sourceNotes": "Reported event/phase order only. Do not interpret report phases as a continuous sensor stream.",
        "group": "Report section",
        "record": "Original report timepoint",
        "metrics": "Measured variable",
        "value": "Reported value",
        "unit": "Original unit",
        "qualifier": "Qualifier / range",
        "missing": "NOT REPORTED",
        "chart": "SOURCE-DERIVED VALUES  /  NO INTERPOLATION",
        "categoricalComparison": "ORIGINAL REPORT PHASE COMPARISON · NOT UTC",
        "hostedScenario": "SIMULATED patient exploration",
        "hostedBriefing": "SIMULATED scenario briefing",
        "hostedArchive": "NASA MA-7 historical archive",
        "hostedScope": "This module preserves its original data/API permissions and source provenance",
        "hostedTimeScope": "Home UTC bounds are not linked to this module; use its own time controls",
        "chartEmpty": "No original numeric values for this variable.",
        "selectMetric": "Bar series",
        "seriesDesc": "One bar per originally reported timepoint. Aggregated means remain reported means.",
        "utcTitle": "UTC observations · authorization required",
        "utcNote": "No UTC records have been supplied by an authorized live-data controller. No artificial sensor output is shown.",
        "utcCount": "{count} source-checked records in the current UTC window",
        "utcEmpty": "NO AUTHORIZED UTC DATA IN THIS TIME RANGE",
        "utcAsk": "Open authenticated Monitoring",
        "utcMetric": "Metric / source",
        "utcTime": "Observed UTC",
        "utcValue": "Value",
        "utcSource": "Source / quality",
        "utcPlot": "SELECT ONE METRIC AND SOURCE TO PLOT",
        "inspectNone": "Select a report timepoint, variable or UTC observation to inspect its original source and quality.",
        "homeInspectTitle": "Mission Workspace properties",
        "inspectCurrent": "Selected object",
        "inspectTimeScope": "UTC scope",
        "inspectAccess": "Data access",
        "homeInspectNoSelection": "Operations overview · no active crew or source selected",
        "homeInspectUTC": "UTC conductor applies to authorized timestamped observations only; NASA MA-7 is separately browsable",
        "homeInspectACL": "Health records require real AETHERION Server authorization; no subject data loaded here",
        "inspectArchive": "Original NASA source (historical, non-live)",
        "inspectUTC": "Authorized timestamped observation (not automatically imported)",
        "inspectSource": "Source",
        "inspectTable": "Table / page",
        "inspectGroup": "Report group",
        "inspectRecord": "Original timepoint",
        "inspectMetric": "Variable",
        "inspectValue": "Value",
        "inspectUnit": "Unit",
        "inspectQualifier": "Qualifier",
        "inspectRange": "Published range",
        "inspectCount": "Reported sample count",
        "inspectUTCValue": "UTC timestamp",
        "inspectVerification": "Verification state",
        "inspectQuality": "Quality",
        "inspectNoUTC": "No precise UTC timestamp supplied by source",
        "footer": "SOURCE FIRST  ·  NO SIMULATED DATA IN THIS HOME WORKSPACE",
        "openOriginal": "NASA original report",
        "archiveUnavailable": "Historical source file could not be loaded; no replacement values generated.",
    },
    "vi": {
        "brand": "AETHERION  /  MISSION OPERATIONS",
        "connection": "Chưa xác minh kết nối",
        "browse": "DUYỆT ĐỐI TƯỢNG",
        "browseSearch": "Tìm đối tượng và chức năng…",
        "utcMetricFilter": "Lọc quan sát UTC theo chỉ số và đơn vị",
        "utcSourceFilter": "Lọc quan sát UTC theo nguồn đã xác minh",
        "utcAllMetrics": "Tất cả nhóm chỉ số",
        "utcAllSources": "Tất cả nguồn đã xác minh",
        "utcChartSeries": "Một chỉ số và đơn vị được chọn · một nguồn được chọn · trạng thái xác minh ở Inspect · chỉ điểm rời rạc · không nội suy",
        "utcChartNeedsFilter": "Chọn một chỉ số/đơn vị và một nguồn để hiển thị một chuỗi. Trạng thái xác minh vẫn ở Inspect.",
        "utcXAxis": "THỜI GIAN · UTC",
        "utcYAxis": "GIÁ TRỊ · {unit}",
        "utcSeriesTitle": "CHUỖI ĐANG CHỌN · {metric} ({unit}) · {source}",

        "inspect": "THUỘC TÍNH  /  NGUỒN",
        "workspace": "KHÔNG GIAN DỮ LIỆU",
        "science": "KHOA HỌC & NGUỒN",
        "clinical": "SỨC KHỎE & CHĂM SÓC",
        "systems": "HỆ THỐNG",
        "mission": "Nhiệm vụ",
        "crew": "Phi hành đoàn",
        "health": "Sức khỏe của tôi",
        "monitor": "Theo dõi",
        "ecg": "Điện tim",
        "assistant": "Hỏi AI",
        "interview": "Hỏi triệu chứng",
        "care": "Hành trình chăm sóc",
        "care_guide": "Hướng dẫn chăm sóc",
        "science_route": "Đài quan sát khoa học",
        "hazards": "Nguy cơ NASA",
        "medical_library": "Thư viện y khoa",
        "atlas": "Cơ thể 3D",
        "settings": "Cài đặt",
        "home": "Không gian điều hành",
        "archive": "NASA MA-7 · bản ghi gốc",
        "utc": "Quan sát UTC",
        "demo": "DEMO GIẢ LẬP",
        "sim": "SIMULATED",
        "real": "NASA MA-7 · 1962",
        "realBadge": "LỊCH SỬ THẬT · NGUỒN NASA",
        "simulationHint": "Năm hồ sơ giả lập tách khỏi bệnh án thực",
        "archiveHint": "83 giá trị đã công bố trong 19 mốc báo cáo NASA",
        "runDemo": "Khám phá Demo giả lập",
        "runArchive": "Mở kho NASA",
        "sourceGuide": "Xem báo cáo NASA gốc",
        "launch": "Mở chức năng",
        "welcome": "Chọn một nguồn hoặc chức năng từ cây bên trái.",
        "welcomeLead": "Không gian hiển thị các số đo lịch sử thật từ NASA và trạng thái thiếu dữ liệu UTC trung thực. Không tạo sinh hiệu trực tiếp giả.",
        "welcomeSource": "Danh mục nguồn",
        "welcomeCount": "{records} mốc báo cáo MA-7 · {values} giá trị ghi nhận",
        "welcomeNoSource": "Bộ nguồn NASA thiếu hoặc không hợp lệ. Có thể mở kho để xem lỗi.",
        "welcomeReal": "Xem các bản ghi NASA MA-7",
        "welcomeUtc": "Xem dữ liệu UTC",
        "homeNotice": "Không đọc hồ sơ người bệnh khi chưa có nguồn được cấp quyền.",
        "time": "TIME CONDUCTOR",
        "timeHelp": "Khoảng UTC dùng chung cho biểu đồ, bảng và Inspect",
        "from": "Từ",
        "to": "Đến",
        "recentDay": "24 giờ",
        "recentWeek": "7 ngày",
        "recentMonth": "30 ngày",
        "apply": "Áp dụng UTC",
        "timeInvalid": "Khoảng UTC không hợp lệ: thời điểm bắt đầu phải trước kết thúc.",
        "timeRangeTooShort": "Khoảng UTC phải dài ít nhất 1 phút.",
        "timeRangeTooLong": "Khoảng UTC không được vượt quá 366 ngày.",
        "timeWindow": "Khoảng UTC: {start} — {end}",
        "timeSource": "Mốc báo cáo MA-7 không có thời điểm UTC tuyệt đối được xác minh. Bộ lọc UTC không tác động vào dữ liệu lịch sử này.",
        "sourceTitle": "Mercury-Atlas 7 · giá trị nguồn NASA",
        "sourceNotes": "Chỉ trình bày mốc/giai đoạn báo cáo gốc; không diễn giải là chuỗi cảm biến liên tục.",
        "group": "Phần báo cáo",
        "record": "Mốc ghi nhận",
        "metrics": "Biến đo",
        "value": "Giá trị gốc",
        "unit": "Đơn vị gốc",
        "qualifier": "Ghi chú / khoảng",
        "missing": "KHÔNG CÔNG BỐ",
        "chart": "GIÁ TRỊ NGUỒN  /  KHÔNG NỘI SUY",
        "categoricalComparison": "ĐỐI CHIẾU GIAI ĐOẠN GỐC · KHÔNG PHẢI UTC",
        "hostedScenario": "Khám phá bệnh nhân SIMULATED",
        "hostedBriefing": "Giới thiệu kịch bản SIMULATED",
        "hostedArchive": "Kho lưu trữ NASA MA-7 thật",
        "hostedScope": "Mô-đun giữ nguyên quyền truy cập API, dữ liệu và nguồn gốc",
        "hostedTimeScope": "Khoảng UTC ở Home chưa nối với mô-đun này; dùng bộ lọc riêng của mô-đun",
        "chartEmpty": "Không có số đo gốc dạng số cho biến này.",
        "selectMetric": "Biến của biểu đồ",
        "seriesDesc": "Mỗi cột là một mốc gốc; các giá trị trung bình giữ đúng nghĩa trung bình.",
        "utcTitle": "Quan sát UTC · yêu cầu quyền truy cập",
        "utcNote": "Chưa có bản ghi UTC nào được bộ điều khiển có quyền cấp vào. Không vẽ tín hiệu cảm biến giả.",
        "utcCount": "{count} bản ghi có nguồn trong khoảng UTC",
        "utcEmpty": "KHÔNG CÓ DỮ LIỆU UTC ĐƯỢC CẤP QUYỀN",
        "utcAsk": "Mở Theo dõi có xác thực",
        "utcMetric": "Chỉ số / nguồn",
        "utcTime": "Ghi nhận UTC",
        "utcValue": "Giá trị",
        "utcSource": "Nguồn / chất lượng",
        "utcPlot": "CHỌN MỘT CHỈ SỐ VÀ NGUỒN ĐỂ VẼ",
        "inspectNone": "Chọn mốc, biến hoặc quan sát UTC để xem nguồn và mức độ xác minh.",
        "homeInspectTitle": "Thuộc tính không gian điều hành",
        "inspectCurrent": "Đối tượng đang chọn",
        "inspectTimeScope": "Phạm vi UTC",
        "inspectAccess": "Quyền truy cập",
        "homeInspectNoSelection": "Tổng quan điều hành · chưa chọn phi hành đoàn hoặc nguồn đo",
        "homeInspectUTC": "Time Conductor chỉ lọc quan sát có timestamp được cấp quyền; NASA MA-7 là kho riêng",
        "homeInspectACL": "Hồ sơ sức khỏe yêu cầu phân quyền từ AETHERION Server; chưa nạp dữ liệu cá nhân ở đây",
        "inspectArchive": "Nguồn NASA lịch sử thật, không trực tiếp",
        "inspectUTC": "Quan sát có dấu thời gian và quyền xác thực (không tự nhập)",
        "inspectSource": "Nguồn",
        "inspectTable": "Bảng / trang",
        "inspectGroup": "Nhóm báo cáo",
        "inspectRecord": "Mốc gốc",
        "inspectMetric": "Biến",
        "inspectValue": "Giá trị",
        "inspectUnit": "Đơn vị",
        "inspectQualifier": "Chú thích",
        "inspectRange": "Khoảng công bố",
        "inspectCount": "Số lượt đo trong báo cáo",
        "inspectUTCValue": "Dấu thời gian UTC",
        "inspectVerification": "Trạng thái xác minh",
        "inspectQuality": "Chất lượng",
        "inspectNoUTC": "Nguồn không cung cấp thời điểm UTC chính xác",
        "footer": "CÓ NGUỒN · KHÔNG ĐƯA DỮ LIỆU GIẢ LẬP VÀO TRANG CHÍNH",
        "openOriginal": "Báo cáo NASA gốc",
        "archiveUnavailable": "Không thể đọc nguồn NASA; không tạo số liệu thay thế.",
    },
}


def _locale(raw: object) -> str:
    return "en" if str(raw).lower().startswith("en") else "vi"


def _safe_utc(raw: object) -> datetime | None:
    """Only literal UTC ISO8601 timestamps; NEVER convert uncertain local time."""
    if not isinstance(raw, str) or not re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?(?:Z|\+00:00)", raw
    ):
        return None
    try:
        timestamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return timestamp.astimezone(timezone.utc)
    except (TypeError, ValueError, OverflowError):
        return None


def _observed_utc(row: dict) -> datetime | None:
    return _safe_utc(row.get("timestamp_utc")) if isinstance(row, dict) else None


class UtcSamplePlot(QWidget):
    """UTC scatter plot: measured timestamps are positioned on a real time axis.

    Samples are drawn as independent points, never connected or interpolated.
    Clicking a point selects the corresponding row for source inspection.
    """

    sample_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(176)
        self.setObjectName("opsUtcSamplePlot")
        self.setMouseTracking(True)
        self._points: tuple[dict, ...] = ()
        self._index_offset = 0
        self._positions: tuple[tuple[float, float, int], ...] = ()
        self._plotted_by_index: dict[int, dict] = {}
        self._theme = "daybreak"
        self._mode = "light"
        self._time_axis_label = "TIME · UTC"
        self._value_axis_label = ""
        self._time_bounds: tuple[float, float] | None = None

    def set_points(
        self, points, theme="daybreak", mode="light", *, index_offset=0,
        time_axis_label=None, value_axis_label=None, time_bounds=None
    ):
        self._points = tuple(points)
        self._index_offset = max(0, int(index_offset))
        self._theme = theme
        self._mode = mode
        if time_axis_label is not None:
            self._time_axis_label = str(time_axis_label)
        if value_axis_label is not None:
            self._value_axis_label = str(value_axis_label)
        if time_bounds is not None:
            try:
                start, end = map(float, time_bounds)
            except (TypeError, ValueError, OverflowError):
                self._time_bounds = None
            else:
                self._time_bounds = (
                    (start, end)
                    if math.isfinite(start) and math.isfinite(end) and end > start
                    else None
                )
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = palette_for(self._theme, self._mode)
        width, height = self.width(), self.height()
        # Reserve a compact header for the selected value/unit and an explicit UTC x-axis label.
        plot = QRectF(58, 27, max(1, width - 76), max(1, height - 69))
        positions = []
        plotted = []
        for local_index, row in enumerate(self._points):
            value, epoch = row.get("value"), row.get("_epoch")
            if (isinstance(value, (int, float)) and math.isfinite(float(value))
                    and isinstance(epoch, (int, float))
                    and math.isfinite(float(epoch))):
                plotted.append(
                    (row, float(value), float(epoch),
                     self._index_offset + local_index)
                )
        points = tuple(plotted)
        painter.setPen(QColor(pal.text))
        painter.drawText(
            QRectF(plot.left(), 2, plot.width(), 18),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self._value_axis_label,
        )
        painter.drawText(
            QRectF(max(plot.left(), plot.right() - 120), plot.bottom() + 22, 120, 16),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            self._time_axis_label,
        )
        if not points:
            painter.setPen(QColor(pal.muted))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "—")
            self._positions = ()
            painter.end()
            return

        values = [value for _row, value, _epoch, _index in points]
        times = [epoch for _row, _value, epoch, _index in points]
        low, high = min(values), max(values)
        if low == high:
            padding = max(abs(low) * .05, 1.0)
            low, high = low - padding, high + padding
        if self._time_bounds is not None:
            first_time, last_time = self._time_bounds
        else:
            first_time, last_time = min(times), max(times)
        time_span = last_time - first_time

        grid = QColor(pal.border)
        grid.setAlpha(190)
        painter.setPen(QPen(grid, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for index in range(5):
            fraction = index / 4
            y = plot.top() + fraction * plot.height()
            painter.drawLine(int(plot.left()), int(y), int(plot.right()), int(y))
            tick_value = high - fraction * (high - low)
            painter.setPen(QColor(pal.muted))
            painter.drawText(
                QRectF(0, y - 9, 52, 18),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{tick_value:.3g}",
            )
            painter.setPen(QPen(grid, 1))

        tick_fractions = (0.0, .5, 1.0) if time_span > 0 else (.5,)
        if time_span >= 31_536_000:
            tick_label_format = "%Y-%m"
        elif time_span >= 86_400:
            tick_label_format = "%m-%d %H:%M"
        else:
            tick_label_format = "%H:%M:%S"
        for fraction in tick_fractions:
            x = plot.left() + fraction * plot.width()
            painter.setPen(QPen(grid, 1))
            painter.drawLine(int(x), int(plot.top()), int(x), int(plot.bottom()))
            tick_time = first_time + fraction * time_span
            label = datetime.fromtimestamp(tick_time, tz=timezone.utc).strftime(
                tick_label_format
            )
            painter.setPen(QColor(pal.muted))
            label_width = min(98, max(54, int(plot.width() / 3)))
            label_left = min(
                max(0, x - label_width / 2),
                max(0, width - label_width),
            )
            painter.drawText(
                QRectF(label_left, plot.bottom() + 5, label_width, 17),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                label,
            )

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(pal.accent))
        radius = 4.5
        self._plotted_by_index = {}
        for row, value, epoch, source_index in points:
            x_fraction = .5 if time_span == 0 else (epoch - first_time) / time_span
            y_fraction = (value - low) / (high - low)
            x = plot.left() + x_fraction * plot.width()
            y = plot.bottom() - y_fraction * plot.height()
            painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
            positions.append((x, y, source_index))
            self._plotted_by_index[source_index] = row

        self._positions = tuple(positions)
        painter.end()

    def _nearest_position(self, x, y):
        if not self._positions:
            return None
        nearest = min(self._positions, key=lambda point:
                      (point[0] - x) ** 2 + (point[1] - y) ** 2)
        return nearest if (nearest[0] - x) ** 2 + (nearest[1] - y) ** 2 <= 144 else None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            hit = self._nearest_position(event.position().x(), event.position().y())
            if hit is not None:
                self.sample_selected.emit(hit[2])
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        hit = self._nearest_position(event.position().x(), event.position().y())
        if hit is None:
            self.setToolTip("")
        else:
            row = self._plotted_by_index.get(hit[2])
            if row is None:
                self.setToolTip("")
                super().mouseMoveEvent(event)
                return
            self.setToolTip(
                f'{row["timestamp_utc"]} · {row["value"]} {row["unit"]} · '
                f'{row["source_id"]}'
            )
        super().mouseMoveEvent(event)


class MissionOperationsHome(QWidget):
    """Functional native object browser, coordinated science views and inspector."""

    route_requested = Signal(str)
    simulated_demo_requested = Signal()
    nasa_archive_requested = Signal()
    time_range_changed = Signal(str, str)

    def __init__(self, parent=None, *, locale="en", reduce_motion=False):
        super().__init__(parent)
        self.language = _locale(locale)
        self.reduce_motion = bool(reduce_motion)
        self.theme = "daybreak"
        self.mode = "light"
        self.source_data: dict | None = None
        self.source_error = ""
        self._selection: tuple[str, str] = ("home", "")
        self._utc_rows: tuple[dict, ...] = ()
        self._filtered_utc: tuple[dict, ...] = ()
        self._selected_nasa_record: dict | None = None
        self._selected_nasa_metric: str | None = None
        self._active_utc_row: dict | None = None
        self._objects: dict[str, QTreeWidgetItem] = {}
        # Persistent central feature pages; original widgets keep their auth/API.
        self._hosted_features: dict[str, QWidget] = {}
        self.setObjectName("missionOperationsHome")
        self._load_historical_source()

        shell = QVBoxLayout(self)
        shell.setContentsMargins(12, 9, 12, 8)
        shell.setSpacing(7)

        command = QFrame()
        command.setObjectName("surface")
        command_row = QHBoxLayout(command)
        command_row.setContentsMargins(12, 6, 12, 6)
        self.brand = QLabel()
        self.brand.setObjectName("eyebrow")
        command_row.addWidget(self.brand, 1)
        self.status = QLabel()
        self.status.setObjectName("connectionPill")
        command_row.addWidget(self.status)
        self.demo = QPushButton()
        self.demo.setMinimumHeight(39)
        self.demo.setObjectName("primaryAction")
        self.demo.clicked.connect(self.simulated_demo_requested.emit)
        command_row.addWidget(self.demo)
        shell.addWidget(command)

        # One shared time control owns the UTC window. All UTC views use it.
        conductor = QFrame()
        conductor.setObjectName("contentPanel")
        self.time_conductor = conductor
        conductor_box = QVBoxLayout(conductor)
        conductor_box.setContentsMargins(10, 5, 10, 5)
        conductor_box.setSpacing(2)
        conductor_row = QHBoxLayout()
        conductor_row.setSpacing(7)
        conductor_box.addLayout(conductor_row)
        self.conductor_heading = QLabel()
        self.conductor_heading.setObjectName("eyebrow")
        conductor_row.addWidget(self.conductor_heading)
        self.from_label = QLabel()
        conductor_row.addWidget(self.from_label)
        self.begin_utc = QDateTimeEdit()
        self.begin_utc.setTimeZone(QTimeZone.utc())
        self.begin_utc.setCalendarPopup(True)
        self.begin_utc.setDisplayFormat("yyyy-MM-dd HH:mm 'UTC'")
        self.begin_utc.setMinimumWidth(161)
        conductor_row.addWidget(self.begin_utc)
        self.to_label = QLabel()
        conductor_row.addWidget(self.to_label)
        self.end_utc = QDateTimeEdit()
        self.end_utc.setTimeZone(QTimeZone.utc())
        self.end_utc.setCalendarPopup(True)
        self.end_utc.setDisplayFormat("yyyy-MM-dd HH:mm 'UTC'")
        self.end_utc.setMinimumWidth(161)
        conductor_row.addWidget(self.end_utc)
        end = QDateTime.currentDateTimeUtc()
        self.end_utc.setDateTime(end)
        self.begin_utc.setDateTime(end.addDays(-7))
        self.preset_day = QPushButton()
        self.preset_week = QPushButton()
        self.preset_month = QPushButton()
        for button, days in ((self.preset_day, 1),
                             (self.preset_week, 7), (self.preset_month, 30)):
            button.setObjectName("navButton")
            button.clicked.connect(lambda checked=False, span=days:
                                   self.set_recent_days(span))
            conductor_row.addWidget(button)
        self.apply_button = QPushButton()
        self.apply_button.setObjectName("navButton")
        self.apply_button.clicked.connect(self.apply_utc_window)
        conductor_row.addWidget(self.apply_button)
        self.window_status = QLabel()
        self.window_status.setObjectName("pageHint")
        self.window_status.setWordWrap(True)
        conductor_box.addWidget(self.window_status)

        horizontal = QSplitter(Qt.Orientation.Horizontal)
        horizontal.setHandleWidth(5)
        horizontal.setChildrenCollapsible(False)
        shell.addWidget(horizontal, 1)
        self.splitter = horizontal

        # Browse: meaningful object selection previews native data, double click
        # opens existing authenticated feature route without changing its ACL.
        left = QFrame()
        left.setObjectName("contentPanel")
        nav_layout = QVBoxLayout(left)
        left.setMinimumWidth(177)
        left.setMaximumWidth(255)
        nav_layout.setContentsMargins(8, 9, 8, 9)
        self.browse_heading = QLabel()
        self.browse_heading.setObjectName("eyebrow")
        nav_layout.addWidget(self.browse_heading)
        self.browse_search = QLineEdit()
        self.browse_search.setClearButtonEnabled(True)
        self.browse_search.setMaxLength(100)
        self.browse_search.textChanged.connect(self._filter_browse)
        nav_layout.addWidget(self.browse_search)
        self.navigator = QTreeWidget()
        self.navigator.setHeaderHidden(True)
        self.navigator.setUniformRowHeights(True)
        self.navigator.setMinimumWidth(172)
        self.navigator.itemSelectionChanged.connect(self._browse_selected)
        self.navigator.itemDoubleClicked.connect(self._browse_open)
        nav_layout.addWidget(self.navigator, 1)
        self.open_action = QPushButton()
        self.open_action.setObjectName("navButton")
        self.open_action.clicked.connect(self._open_selected)
        nav_layout.addWidget(self.open_action)
        horizontal.addWidget(left)

        middle = QFrame()
        middle.setObjectName("contentPanel")
        middle.setMinimumWidth(405)
        middle_layout = QVBoxLayout(middle)
        middle_layout.setContentsMargins(8, 9, 8, 9)
        self.workspace_heading = QLabel()
        self.workspace_heading.setObjectName("eyebrow")
        middle_layout.addWidget(self.workspace_heading)
        self.workspace_stack = QStackedWidget()
        middle_layout.addWidget(self.workspace_stack, 1)
        horizontal.addWidget(middle)

        overview = QWidget()
        ov = QVBoxLayout(overview)
        ov.setContentsMargins(12, 8, 12, 8)
        ov.setSpacing(8)
        self.welcome = QLabel()
        self.welcome.setObjectName("heading")
        self.welcome.setWordWrap(True)
        ov.addWidget(self.welcome)
        self.welcome_lead = QLabel()
        self.welcome_lead.setObjectName("pageHint")
        self.welcome_lead.setWordWrap(True)
        ov.addWidget(self.welcome_lead)
        self.source_count = QLabel()
        self.source_count.setObjectName("heading")
        self.source_count.setWordWrap(True)
        ov.addWidget(self.source_count)
        self.provenance = QLabel()
        self.provenance.setObjectName("pageHint")
        self.provenance.setWordWrap(True)
        ov.addWidget(self.provenance)
        overview_actions = QHBoxLayout()
        self.nasa_view = QPushButton()
        self.nasa_view.setObjectName("navButton")
        self.nasa_view.clicked.connect(lambda: self._choose("archive"))
        overview_actions.addWidget(self.nasa_view)
        self.utc_view = QPushButton()
        self.utc_view.setObjectName("navButton")
        self.utc_view.clicked.connect(lambda: self._choose("utc"))
        overview_actions.addWidget(self.utc_view)
        self.nasa_full = QPushButton()
        self.nasa_full.setObjectName("primaryAction")
        self.nasa_full.clicked.connect(self.nasa_archive_requested.emit)
        overview_actions.addWidget(self.nasa_full)
        ov.addLayout(overview_actions)
        self.welcome_note = QLabel()
        self.welcome_note.setObjectName("pageHint")
        self.welcome_note.setWordWrap(True)
        ov.addWidget(self.welcome_note)
        ov.addStretch(1)
        self.workspace_stack.addWidget(overview)

        archive = QWidget()
        archive_layout = QVBoxLayout(archive)
        archive_layout.setContentsMargins(4, 4, 4, 4)
        archive_layout.setSpacing(5)
        self.archive_title = QLabel()
        self.archive_title.setObjectName("heading")
        archive_layout.addWidget(self.archive_title)
        self.archive_caveat = QLabel()
        self.archive_caveat.setObjectName("pageHint")
        self.archive_caveat.setWordWrap(True)
        archive_layout.addWidget(self.archive_caveat)
        self.group_selector = QComboBox()
        self.group_selector.currentIndexChanged.connect(self._load_report_group)
        archive_layout.addWidget(self.group_selector)
        archive_split = QSplitter(Qt.Orientation.Vertical)
        self.records = QListWidget()
        self.records.setMinimumHeight(78)
        self.records.currentRowChanged.connect(self._select_report_record)
        archive_split.addWidget(self.records)
        self.measurements = QTableWidget(0, 4)
        self.measurements.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.measurements.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.measurements.setAlternatingRowColors(True)
        self.measurements.verticalHeader().hide()
        self.measurements.itemSelectionChanged.connect(self._select_report_metric)
        self.measurements.horizontalHeader().setStretchLastSection(True)
        archive_split.addWidget(self.measurements)
        archive_split.setSizes([100, 220])
        archive_layout.addWidget(archive_split, 1)
        self.metric_selector = QComboBox()
        self.metric_selector.currentIndexChanged.connect(self._update_report_chart)
        archive_layout.addWidget(self.metric_selector)
        # The primary source comparison uses original categorical report labels.
        # No unlabeled bars or invented absolute UTC positions.
        self.report_comparison_heading = QLabel()
        self.report_comparison_heading.setObjectName("eyebrow")
        archive_layout.addWidget(self.report_comparison_heading)
        self.report_comparison = QTableWidget(0, 4)
        self.report_comparison.setObjectName("opsReportPhaseComparison")
        self.report_comparison.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.report_comparison.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.report_comparison.verticalHeader().hide()
        self.report_comparison.setAlternatingRowColors(True)
        self.report_comparison.horizontalHeader().setStretchLastSection(True)
        self.report_comparison.setMinimumHeight(96)
        self.report_comparison.itemSelectionChanged.connect(
            self._select_comparison_phase)
        archive_layout.addWidget(self.report_comparison, 1)
        self.archive_note = QLabel()
        self.archive_note.setObjectName("pageHint")
        self.archive_note.setWordWrap(True)
        archive_layout.addWidget(self.archive_note)
        self.workspace_stack.addWidget(archive)

        utc = QWidget()
        utc_layout = QVBoxLayout(utc)
        utc_layout.setContentsMargins(4, 4, 4, 4)
        utc_layout.setSpacing(7)
        self.utc_heading = QLabel()
        self.utc_heading.setObjectName("heading")
        utc_layout.addWidget(self.utc_heading)
        self.utc_note = QLabel()
        self.utc_note.setObjectName("pageHint")
        self.utc_note.setWordWrap(True)
        utc_layout.addWidget(self.utc_note)
        self.utc_count = QLabel()
        self.utc_count.setObjectName("eyebrow")
        utc_layout.addWidget(self.utc_count)
        utc_filters = QHBoxLayout()
        self.utc_metric_selector = QComboBox()
        self.utc_metric_selector.currentIndexChanged.connect(self._refresh_utc)
        utc_filters.addWidget(self.utc_metric_selector, 1)
        self.utc_source_selector = QComboBox()
        self.utc_source_selector.currentIndexChanged.connect(self._refresh_utc)
        utc_filters.addWidget(self.utc_source_selector, 1)
        utc_layout.addLayout(utc_filters)
        self.utc_table = QTableWidget(0, 4)
        self.utc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.utc_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.utc_table.setAlternatingRowColors(True)
        self.utc_table.verticalHeader().hide()
        self.utc_table.horizontalHeader().setStretchLastSection(True)
        self.utc_table.itemSelectionChanged.connect(self._select_utc_row)
        utc_layout.addWidget(self.utc_table, 1)
        self.utc_chart_heading = QLabel()
        self.utc_chart_heading.setObjectName("eyebrow")
        self.utc_chart_heading.setWordWrap(True)
        utc_layout.addWidget(self.utc_chart_heading)
        self.utc_chart = UtcSamplePlot()
        self.utc_chart.sample_selected.connect(self._select_utc_plot_point)
        utc_layout.addWidget(self.utc_chart)
        self.utc_chart_note = QLabel()
        self.utc_chart_note.setObjectName("pageHint")
        self.utc_chart_note.setWordWrap(True)
        utc_layout.addWidget(self.utc_chart_note)
        self.utc_empty = QLabel()
        self.utc_empty.setObjectName("pageHint")
        self.utc_empty.setWordWrap(True)
        utc_layout.addWidget(self.utc_empty)
        self.open_monitor = QPushButton()
        self.open_monitor.setObjectName("navButton")
        self.open_monitor.clicked.connect(lambda: self.route_requested.emit("monitor"))
        utc_layout.addWidget(self.open_monitor)
        self.workspace_stack.addWidget(utc)

        preview = QWidget()
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(13, 9, 13, 9)
        self.preview_heading = QLabel()
        self.preview_heading.setObjectName("heading")
        self.preview_heading.setWordWrap(True)
        preview_layout.addWidget(self.preview_heading)
        self.preview_summary = QLabel()
        self.preview_summary.setObjectName("pageHint")
        self.preview_summary.setWordWrap(True)
        preview_layout.addWidget(self.preview_summary)
        self.preview_button = QPushButton()
        self.preview_button.setObjectName("primaryAction")
        self.preview_button.clicked.connect(self._open_selected)
        preview_layout.addWidget(self.preview_button)
        preview_layout.addStretch()
        self.workspace_stack.addWidget(preview)

        # Inspect: displays the *same* selected report row or UTC observation.
        right = QFrame()
        right.setObjectName("contentPanel")
        # INSPECT must remain visible and horizontally scrollable at 1040px.
        # Do not auto-hide it based on window width.
        right.setMinimumWidth(205)
        right.setMaximumWidth(325)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 9, 8, 9)
        self.inspect_heading = QLabel()
        self.inspect_heading.setObjectName("eyebrow")
        right_layout.addWidget(self.inspect_heading)
        self.inspect_title = QLabel()
        self.inspect_title.setObjectName("heading")
        self.inspect_title.setWordWrap(True)
        right_layout.addWidget(self.inspect_title)
        self.inspector = QTableWidget(0, 2)
        self.inspector.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.inspector.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.inspector.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.inspector.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.inspector.setWordWrap(True)
        self.inspector.verticalHeader().hide()
        self.inspector.horizontalHeader().hide()
        self.inspector.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.inspector, 1)
        self.source_link = QPushButton()
        self.source_link.setObjectName("navButton")
        self.source_link.clicked.connect(self.open_nasa_original)
        right_layout.addWidget(self.source_link)
        horizontal.addWidget(right)
        horizontal.setStretchFactor(0, 0)
        horizontal.setStretchFactor(1, 1)
        horizontal.setStretchFactor(2, 0)
        horizontal.setSizes([198, 600, 224])

        # Open MCT-style conductor is a persistent strip BELOW data views,
        # not a full-width header that reduces the available workspace.
        shell.addWidget(conductor)

        self.footer = QLabel()
        self.footer.setObjectName("pageHint")
        shell.addWidget(self.footer)

        self.set_locale(self.language)
        self.set_visuals()
        # Home is the operational overview. Historical NASA is one source
        # available from Browse, not a silently selected active mission.
        self._choose("home")
        self.apply_utc_window()

    def _load_historical_source(self):
        try:
            self.source_data = load_real_nasa_data()
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.source_data = None
            self.source_error = type(error).__name__

    def _t(self, key, **fields):
        value = TEXT[self.language][key]
        return value.format(**fields) if fields else value

    def _archive_counts(self):
        if self.source_data is None:
            return 0, 0
        groups = self.source_data["groups"]
        return (
            sum(len(g["records"]) for g in groups),
            sum(1 for group in groups for r in group["records"]
                for m in r["measures"].values() if m["value"] is not None),
        )

    def _fill_tree(self):
        selected = self._selection[0]
        self.navigator.blockSignals(True)
        self.navigator.clear()
        self._objects = {}
        selected = {
            "simulated_briefing": "demo",
            "synthetic_patient": "demo",
            "nasa_archive": "archive",
        }.get(selected, selected)
        groups = (
            ("workspace", (("home", "home"), ("demo", "demo"),
                           ("archive", "archive"), ("utc", "utc"))),
            ("clinical", tuple((route, route) for route in
                         ("mission", "crew", "health", "monitor", "ecg",
                          "assistant", "interview", "care", "care_guide"))),
            ("science", tuple((route, "science_route" if route == "science" else route)
                              for route in ("science", "hazards", "medical_library", "atlas"))),
            ("systems", (("settings", "settings"),)),
        )
        for name, rows in groups:
            parent = QTreeWidgetItem([self._t(name)])
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.navigator.addTopLevelItem(parent)
            for route, title in rows:
                item = QTreeWidgetItem([self._t(title)])
                item.setData(0, Qt.ItemDataRole.UserRole, route)
                parent.addChild(item)
                self._objects[route] = item
            parent.setExpanded(True)
        self.navigator.blockSignals(False)
        self._filter_browse(self.browse_search.text())
        if selected in self._objects:
            self.navigator.setCurrentItem(self._objects[selected])

    def _filter_browse(self, text):
        query = str(text).strip().casefold()
        for i in range(self.navigator.topLevelItemCount()):
            parent = self.navigator.topLevelItem(i)
            shown = 0
            for j in range(parent.childCount()):
                child = parent.child(j)
                visible = not query or query in child.text(0).casefold()
                child.setHidden(not visible)
                shown += int(visible)
            parent.setHidden(shown == 0)

    def _choose(self, route):
        if route not in self._objects:
            return
        self._selection = (route, "")
        self.navigator.blockSignals(True)
        self.navigator.setCurrentItem(self._objects[route])
        self.navigator.blockSignals(False)
        self._select_workspace(route)

    def _browse_selected(self):
        selected = self.navigator.selectedItems()
        item = selected[0] if selected else self.navigator.currentItem()
        if item is None:
            return
        if self.navigator.currentItem() is not item:
            self.navigator.blockSignals(True)
            self.navigator.setCurrentItem(item)
            self.navigator.blockSignals(False)
        route = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(route, str):
            if route in ROUTE_IDS:
                # Main preserves each module's refresh, authorization and data
                # contracts; its handler will show the page in this central stack.
                self.route_requested.emit(route)
            else:
                self._selection = (route, "")
                self._select_workspace(route)

    def _browse_open(self, item, _column):
        route = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(route, str):
            self._open_route(route)

    def _open_selected(self):
        self._open_route(self._selection[0])

    def _open_route(self, route):
        if route == "demo":
            self.simulated_demo_requested.emit()
        elif route == "archive":
            self.nasa_archive_requested.emit()
        elif route == "utc":
            self.route_requested.emit("monitor")
        elif route == "home":
            self._choose("home")
        elif route in ROUTE_IDS:
            self.route_requested.emit(route)

    def attach_feature(self, route: str, widget: QWidget):
        """Mount a real native QWidget inside this persistent operations shell.

        The host must first remove it from any previous QStackedWidget.
        No PatientDemo/Monitor API is patched or bypassed.
        """
        if route not in ROUTE_IDS and route not in (
                "simulated_briefing", "synthetic_patient", "nasa_archive"):
            raise ValueError(f"Unsupported operations route: {route}")
        if not isinstance(widget, QWidget):
            raise TypeError("A native QWidget is required")
        if self.workspace_stack.indexOf(widget) < 0:
            self.workspace_stack.addWidget(widget)
        self._hosted_features[route] = widget

    def show_hosted(self, route: str):
        """Show an existing feature without dropping Browse/Inspect/Conductor."""
        if route not in self._hosted_features:
            return False
        self._selection = (route, "")
        browse_route = {
            "simulated_briefing": "demo",
            "synthetic_patient": "demo",
            "nasa_archive": "archive",
        }.get(route, route)
        if browse_route in self._objects:
            self.navigator.blockSignals(True)
            self.navigator.setCurrentItem(self._objects[browse_route])
            self.navigator.blockSignals(False)
        self._select_workspace(route)
        return True

    def show_overview(self):
        self._choose("home")

    def _select_workspace(self, route):
        self._active_utc_row = None
        # Q-0477 Monitor owns an independent conductor until a shared-bounds
        # adapter is accepted. Keep exactly one visible time control at a time.
        self.time_conductor.setVisible(route != "monitor")
        if route in self._hosted_features:
            self.workspace_stack.setCurrentWidget(self._hosted_features[route])
            label = (self._t(route) if route in TEXT[self.language]
                     else self._t("hostedScenario") if route == "synthetic_patient"
                     else self._t("hostedBriefing") if route == "simulated_briefing"
                     else self._t("hostedArchive"))
            self._inspect(label, [
                ("inspectCurrent", label),
                ("inspectAccess", self._t("hostedScope")),
                ("inspectTimeScope", self._t("hostedTimeScope")),
            ])
        elif route == "home":
            self.workspace_stack.setCurrentIndex(0)
            self._inspect(self._t("homeInspectTitle"), [
                ("inspectCurrent", self._t("homeInspectNoSelection")),
                ("inspectTimeScope", self._t("homeInspectUTC")),
                ("inspectAccess", self._t("homeInspectACL")),
            ])
        elif route == "archive":
            self.workspace_stack.setCurrentIndex(1)
            self._load_report_group()
        elif route == "utc":
            self.workspace_stack.setCurrentIndex(2)
            self._refresh_utc()
        elif route == "demo":
            self.workspace_stack.setCurrentIndex(3)
            self.preview_heading.setText(self._t("demo"))
            self.preview_summary.setText(self._t("hostedBriefing"))
            self._inspect(self._t("demo"), [
                ("inspectAccess", self._t("sim")),
                ("inspectTimeScope", self._t("hostedTimeScope")),
            ])
        else:
            self.workspace_stack.setCurrentIndex(3)
            self.preview_heading.setText(self._t(route if route != "science"
                                                  else "science_route"))
            self.preview_summary.setText(self._t("homeNotice"))
            self._inspect(self.preview_heading.text(), [
                ("inspectVerification", self._t("homeNotice")),
            ])
        self.open_action.setEnabled(
            route in ROUTE_IDS or route in ("archive", "utc", "demo")
        )
        self.preview_button.setText(self._t("launch"))

    def _load_report_group(self, *_):
        self.records.blockSignals(True)
        self.records.clear()
        self.group_selector.blockSignals(True)
        if self.group_selector.count() == 0:
            for group in (self.source_data or {}).get("groups", []):
                self.group_selector.addItem(group["title"][self.language], group["id"])
        else:
            for ix, group in enumerate((self.source_data or {}).get("groups", [])):
                self.group_selector.setItemText(ix, group["title"][self.language])
        self.group_selector.blockSignals(False)
        index = self.group_selector.currentIndex()
        if self.source_data and 0 <= index < len(self.source_data["groups"]):
            group = self.source_data["groups"][index]
            for record in group["records"]:
                self.records.addItem(record["title"][self.language])
        self.records.blockSignals(False)
        self.records.setCurrentRow(0)
        self._select_report_record(0)

    def _selected_group(self):
        index = self.group_selector.currentIndex()
        if self.source_data and 0 <= index < len(self.source_data["groups"]):
            return self.source_data["groups"][index]
        return None

    def _select_report_record(self, index):
        group = self._selected_group()
        if not group or not 0 <= index < len(group["records"]):
            self._selected_nasa_record = None
            self.measurements.setRowCount(0)
            self._inspect(self._t("archiveUnavailable"), [])
            return
        record = group["records"][index]
        self._selected_nasa_record = record
        self.measurements.blockSignals(True)
        self.measurements.setRowCount(0)
        for metric_id, observed in record["measures"].items():
            row = self.measurements.rowCount()
            self.measurements.insertRow(row)
            value = observed["value"]
            cells = (
                self.source_data["metric_names"][metric_id][self.language],
                str(value) if value is not None else self._t("missing"),
                observed["unit"],
                str(observed.get("qualifier") or "—"),
            )
            for column, cell in enumerate(cells):
                item = QTableWidgetItem(cell)
                item.setData(Qt.ItemDataRole.UserRole, metric_id)
                self.measurements.setItem(row, column, item)
        self.measurements.blockSignals(False)
        self.metric_selector.blockSignals(True)
        old_metric = self.metric_selector.currentData()
        self.metric_selector.clear()
        # A source group's measures may differ among timepoints.
        keys = tuple(dict.fromkeys(k for row in group["records"]
                                   for k in row["measures"]))
        for key in keys:
            self.metric_selector.addItem(
                self.source_data["metric_names"][key][self.language], key)
        old_index = self.metric_selector.findData(old_metric)
        self.metric_selector.setCurrentIndex(old_index if old_index >= 0 else 0)
        self.metric_selector.blockSignals(False)
        self._update_report_chart()
        if self.measurements.rowCount():
            selected_metric = self.metric_selector.currentData()
            matched_row = next((
                row for row in range(self.measurements.rowCount())
                if self.measurements.item(row, 0).data(Qt.ItemDataRole.UserRole)
                == selected_metric
            ), 0)
            self.measurements.selectRow(matched_row)
        self._select_report_metric()

    def _select_report_metric(self):
        group, record = self._selected_group(), self._selected_nasa_record
        if not group or not record:
            return
        row = self.measurements.currentRow()
        if row < 0 or not self.measurements.item(row, 0):
            return
        metric_id = self.measurements.item(row, 0).data(Qt.ItemDataRole.UserRole)
        # A selected source measurement drives the categorical comparison
        # metric too, so the right Inspect and phase table never disagree.
        comparison_index = self.metric_selector.findData(metric_id)
        if comparison_index >= 0 and self.metric_selector.currentIndex() != comparison_index:
            self.metric_selector.setCurrentIndex(comparison_index)
        observed = record["measures"][metric_id]
        self._selected_nasa_metric = metric_id
        self._inspect(self.source_data["metric_names"][metric_id][self.language], [
            ("inspectSource", self.source_data["source_title"]),
            ("inspectTable", group["table"]),
            ("inspectGroup", group["title"][self.language]),
            ("inspectRecord", record["title"][self.language]),
            ("inspectMetric", metric_id),
            ("inspectValue", str(observed["value"]) if observed["value"] is not None
             else self._t("missing")),
            ("inspectUnit", observed["unit"]),
            ("inspectQualifier", str(observed.get("qualifier") or "—")),
            ("inspectRange", str(observed.get("range") or "—")),
            ("inspectCount", str(observed.get("sample_count") or "—")),
            ("inspectUTCValue", self._t("inspectNoUTC")),
        ])

    def _update_report_chart(self, *_):
        """Comparison table uses categorical source phases, never artificial UTC."""
        group = self._selected_group()
        metric_id = self.metric_selector.currentData()
        self.report_comparison.blockSignals(True)
        self.report_comparison.setRowCount(0)
        if group and isinstance(metric_id, str):
            for record in group["records"]:
                observation = record["measures"].get(metric_id)
                value = observation.get("value") if observation else None
                row = self.report_comparison.rowCount()
                self.report_comparison.insertRow(row)
                cells = (
                    record["title"][self.language],
                    str(value) if value is not None else self._t("missing"),
                    str(observation.get("unit") or "—") if observation else "—",
                    str(observation.get("qualifier") or "—") if observation else "—",
                )
                for column, cell in enumerate(cells):
                    self.report_comparison.setItem(
                        row, column, QTableWidgetItem(cell))
        self.report_comparison.blockSignals(False)

    def _select_comparison_phase(self):
        """Selecting an original phase synchronizes its raw measurement table."""
        row = self.report_comparison.currentRow()
        group = self._selected_group()
        if group is not None and 0 <= row < len(group["records"]):
            self.records.setCurrentRow(row)

    def _inspect(self, title, properties):
        self.inspect_title.setText(title)
        self.inspector.setRowCount(0)
        for field, value in properties:
            row = self.inspector.rowCount()
            self.inspector.insertRow(row)
            self.inspector.setItem(row, 0, QTableWidgetItem(self._t(field)))
            self.inspector.setItem(row, 1, QTableWidgetItem(str(value)))
        self.inspector.resizeRowsToContents()

    def set_recent_days(self, days: int):
        """One UTC conductor applies the same time window to table/chart/inspect."""
        if days not in (1, 7, 30):
            return
        end = QDateTime.currentDateTimeUtc()
        self.begin_utc.setDateTime(end.addDays(-days))
        self.end_utc.setDateTime(end)
        self.apply_utc_window()

    def apply_utc_window(self):
        start, end = self.begin_utc.dateTime(), self.end_utc.dateTime()
        if start >= end:
            self.window_status.setText(self._t("timeInvalid"))
            return
        span_msecs = start.msecsTo(end)
        if span_msecs < MIN_SPAN.total_seconds() * 1000:
            self.window_status.setText(self._t("timeRangeTooShort"))
            return
        if span_msecs > MAX_SPAN.total_seconds() * 1000:
            self.window_status.setText(self._t("timeRangeTooLong"))
            return
        self._start_epoch, self._end_epoch = start.toSecsSinceEpoch(), end.toSecsSinceEpoch()
        self.window_status.setText(self._t(
            "timeWindow",
            start=start.toUTC().toString("yyyy-MM-dd HH:mm:ss"),
            end=end.toUTC().toString("yyyy-MM-dd HH:mm:ss"),
        ))
        self._refresh_utc()
        # The same UTC window is available for future authenticated plot adapters.
        self.time_range_changed.emit(
            start.toUTC().toString(Qt.DateFormat.ISODate),
            end.toUTC().toString(Qt.DateFormat.ISODate),
        )

    def set_verified_observations(self, rows):
        """Optional host-supplied, *already authorized* original UTC observations.

        Never opens a URL or an arbitrary patient DB; no mock data fallback.
        Reject ambiguous timezone, missing source, synthetic flag or non-finite
        values before merging into the shared UTC plot + table.
        """
        valid = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            utc = _observed_utc(row)
            value = row.get("value")
            if (utc is None or row.get("synthetic") is not False
                    or row.get("verification_state") != "VERIFIED"
                    or not isinstance(row.get("source_id"), str)
                    or not row["source_id"].strip()
                    or not isinstance(row.get("metric"), str)
                    or not row["metric"].strip()
                    or not isinstance(row.get("unit"), str)
                    or not row["unit"].strip()
                    or isinstance(value, bool)
                    or not isinstance(value, (float, int))
                    or not math.isfinite(float(value))):
                continue
            accepted = dict(row)
            accepted["_epoch"] = utc.timestamp()
            valid.append(accepted)
        valid.sort(key=lambda row: row["_epoch"])
        self._utc_rows = tuple(valid)
        self._rebuild_utc_filters()
        self._refresh_utc()

    def _rebuild_utc_filters(self):
        """Keep filtering choices synchronized with the exact supplied sources."""
        if not hasattr(self, "utc_metric_selector"):
            return
        metric_choice = self.utc_metric_selector.currentData()
        source_choice = self.utc_source_selector.currentData()
        metric_keys = sorted({(row["metric"], row["unit"])
                              for row in self._utc_rows})
        source_keys = sorted({row["source_id"] for row in self._utc_rows})
        self.utc_metric_selector.blockSignals(True)
        self.utc_source_selector.blockSignals(True)
        self.utc_metric_selector.clear()
        self.utc_source_selector.clear()
        self.utc_metric_selector.addItem(self._t("utcAllMetrics"), None)
        self.utc_source_selector.addItem(self._t("utcAllSources"), None)
        for metric, unit in metric_keys:
            self.utc_metric_selector.addItem(f"{metric} · {unit}", (metric, unit))
        for source in source_keys:
            self.utc_source_selector.addItem(source, source)
        metric_index = self.utc_metric_selector.findData(metric_choice)
        source_index = self.utc_source_selector.findData(source_choice)
        # Auto-select one actual family when initially connected: never plot
        # heterogeneous units or sources on one graph.
        if metric_choice is None and metric_keys:
            metric_index = 1
        if source_choice is None and source_keys:
            source_index = 1
        self.utc_metric_selector.setCurrentIndex(
            metric_index if metric_index >= 0 else 0)
        self.utc_source_selector.setCurrentIndex(
            source_index if source_index >= 0 else 0)
        self.utc_metric_selector.blockSignals(False)
        self.utc_source_selector.blockSignals(False)

    def _refresh_utc(self, *_):
        start = getattr(self, "_start_epoch", None)
        end = getattr(self, "_end_epoch", None)
        if start is None or end is None:
            return
        metric_filter = self.utc_metric_selector.currentData()
        source_filter = self.utc_source_selector.currentData()
        self._filtered_utc = tuple(
            row for row in self._utc_rows
            if start <= row["_epoch"] <= end
            and (metric_filter is None or
                 (row["metric"], row["unit"]) == metric_filter)
            and (source_filter is None or row["source_id"] == source_filter)
        )
        self.utc_table.blockSignals(True)
        self.utc_table.setRowCount(0)
        for record in self._filtered_utc:
            ix = self.utc_table.rowCount()
            self.utc_table.insertRow(ix)
            entries = (
                record["timestamp_utc"],
                record["metric"],
                f'{record["value"]} {record["unit"]}',
                f'{record["source_id"]} · VERIFIED',
            )
            for column, value in enumerate(entries):
                self.utc_table.setItem(ix, column, QTableWidgetItem(value))
        self.utc_table.blockSignals(False)
        self.utc_count.setText(self._t("utcCount", count=len(self._filtered_utc)))
        self.utc_empty.setText(
            self._t("utcEmpty") if not self._filtered_utc else ""
        )
        # One plot never combines unlike metrics, units or sources. The table
        # can show all filtered records, but the chart needs an explicit family.
        series = self._filtered_utc
        index_offset = 0
        if metric_filter is None or source_filter is None:
            series = ()
        else:
            index_offset = max(0, len(series) - 32)
            series = series[index_offset:]
        if metric_filter is not None and source_filter is not None:
            metric, unit = metric_filter
            chart_title = self._t(
                "utcSeriesTitle", metric=metric, unit=unit, source=source_filter
            )
            chart_note = self._t("utcChartSeries")
            value_axis_label = self._t("utcYAxis", unit=unit)
        else:
            chart_title = self._t("utcPlot")
            chart_note = self._t("utcChartNeedsFilter")
            value_axis_label = ""
        time_axis_label = self._t("utcXAxis")
        self.utc_chart_heading.setText(chart_title)
        self.utc_chart.setAccessibleName(chart_title)
        self.utc_chart.setAccessibleDescription(
            " · ".join(label for label in (
                chart_note, time_axis_label, value_axis_label
            ) if label)
        )
        self.utc_chart.set_points(
            series, self.theme, self.mode, index_offset=index_offset,
            time_axis_label=time_axis_label, value_axis_label=value_axis_label,
            time_bounds=(start, end),
        )
        self.utc_chart_note.setText(chart_note)
        self._active_utc_row = None
        if self._filtered_utc and self._selection[0] == "utc":
            self.utc_table.selectRow(0)
            self._select_utc_row()
        elif not self._filtered_utc and self._selection[0] == "utc":
            self._inspect(self._t("utcEmpty"), [])

    def _select_utc_plot_point(self, index):
        if 0 <= index < len(self._filtered_utc):
            self.utc_table.selectRow(index)

    def _select_utc_row(self):
        if self._selection[0] != "utc":
            return
        row = self.utc_table.currentRow()
        if not 0 <= row < len(self._filtered_utc):
            return
        record = self._filtered_utc[row]
        self._active_utc_row = record
        self._inspect(self._t("inspectUTC"), [
            ("inspectUTCValue", record["timestamp_utc"]),
            ("inspectSource", record["source_id"]),
            ("inspectMetric", record["metric"]),
            ("inspectValue", record["value"]),
            ("inspectUnit", record["unit"]),
            ("inspectVerification", record["verification_state"]),
            ("inspectQuality", record.get("quality", "—")),
        ])

    def open_nasa_original(self):
        if self.source_data is None:
            return
        url = str(self.source_data.get("source_url") or "")
        u = urlsplit(url)
        if u.scheme == "https" and u.hostname in ("www.nasa.gov", "nasa.gov"):
            QDesktopServices.openUrl(QUrl(url))

    def set_locale(self, raw):
        self.language = _locale(raw)
        t = self._t
        self.brand.setText(t("brand"))
        self.status.setText(getattr(self, "_connection_text", t("connection")))
        self.demo.setText(t("demo"))
        self.demo.setAccessibleName(t("demo") + " · " + t("sim"))
        self.conductor_heading.setText(t("time"))
        self.from_label.setText(t("from"))
        self.to_label.setText(t("to"))
        self.preset_day.setText(t("recentDay"))
        self.preset_week.setText(t("recentWeek"))
        self.preset_month.setText(t("recentMonth"))
        self.apply_button.setText(t("apply"))
        self.browse_heading.setText(t("browse"))
        self.open_action.setText(t("launch"))
        self.workspace_heading.setText(t("workspace"))
        self.inspect_heading.setText(t("inspect"))
        self.welcome.setText(t("welcome"))
        self.welcome_lead.setText(t("welcomeLead"))
        count, values = self._archive_counts()
        self.source_count.setText(
            t("welcomeCount", records=count, values=values) if count else
            t("welcomeNoSource"))
        self.provenance.setText(t("archiveHint") if count else t("archiveUnavailable"))
        self.nasa_view.setText(t("welcomeReal"))
        self.utc_view.setText(t("welcomeUtc"))
        self.nasa_full.setText(t("runArchive"))
        self.welcome_note.setText(t("homeNotice"))
        self.archive_title.setText(t("sourceTitle"))
        self.archive_caveat.setText(t("timeSource"))
        self.archive_note.setText(t("seriesDesc"))
        self.report_comparison_heading.setText(t("categoricalComparison"))
        self.report_comparison.setHorizontalHeaderLabels(
            [t(k) for k in ("record", "value", "unit", "qualifier")])
        self.utc_heading.setText(t("utcTitle"))
        self.utc_note.setText(t("utcNote"))
        self.utc_empty.setText(t("utcEmpty") if not self._filtered_utc else "")
        self.utc_chart_heading.setText(t("utcPlot"))
        self.utc_chart.setAccessibleName(t("utcPlot"))
        self.utc_chart.setAccessibleDescription(t("utcChartSeries"))
        self.utc_chart_note.setText(t("utcChartSeries"))
        self.open_monitor.setText(t("utcAsk"))
        self.source_link.setText(t("openOriginal"))
        self.source_link.setEnabled(self.source_data is not None)
        self.footer.setText(t("footer"))
        self.measurements.setHorizontalHeaderLabels(
            [t(k) for k in ("metrics", "value", "unit", "qualifier")])
        self.utc_table.setHorizontalHeaderLabels(
            [t(k) for k in ("utcTime", "utcMetric", "utcValue", "utcSource")])
        self.browse_search.setPlaceholderText(t("browseSearch"))
        self.utc_metric_selector.setAccessibleName(t("utcMetricFilter"))
        self.utc_source_selector.setAccessibleName(t("utcSourceFilter"))
        self._rebuild_utc_filters()
        self._refresh_utc()
        self._fill_tree()
        self._load_report_group()
        # Maintain selected object while translating chrome.
        self._select_workspace(self._selection[0])
        self.window_status.setText(t("timeHelp"))
        if hasattr(self, "_start_epoch"):
            self.window_status.setText(t(
                "timeWindow",
                start=self.begin_utc.dateTime().toUTC().toString("yyyy-MM-dd HH:mm:ss"),
                end=self.end_utc.dateTime().toUTC().toString("yyyy-MM-dd HH:mm:ss"),
            ))

    def set_visuals(self, theme=None, reduce_motion=False, mode=None, intensity=48):
        self.reduce_motion = bool(reduce_motion)
        self.theme = theme or "daybreak"
        self.mode = mode or "light"
        self.utc_chart.set_points(self.utc_chart._points, self.theme, self.mode, index_offset=self.utc_chart._index_offset)

    def set_connection_state(self, state):
        # The host only supplies actual /health results. Preserve verbatim.
        self._connection_text = str(state)
        self.status.setText(self._connection_text)


def build_mission_ops_home(parent=None, **kwargs):
    return MissionOperationsHome(parent, **kwargs)
