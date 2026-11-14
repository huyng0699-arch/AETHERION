"""Native, Open-MCT-inspired Mission Operations start workspace.

The native first-view operations workspace and the SIMULATED-data briefing.
The application shell wires typed route signals to existing real screens.
No fabricated status, vitals, diagnosis, astronaut identity or live telemetry.

No fabricated status, vitals, diagnosis, astronaut identity or live telemetry.
A SIMULATED scenario route is separate from real NASA MA-7 archival science.
"""
from __future__ import annotations

import math

from PySide6.QtCore import Qt, Signal, QTimer, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSplitter, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)

ROUTE_IDS = (
    "mission", "health", "monitor", "ecg", "assistant", "interview",
    "care", "science", "hazards", "medical_library", "atlas",
    "crew", "settings",
)

# Semantic local VI/EN catalog. Q-0485 may move this into shared i18n only after
# the current owners of those files explicitly release their leases.
TEXT = {
    "vi": {
        "eyebrow": "TRUY TINH  /  MISSION OPERATIONS",
        "title": "Trung tâm điều hành",
        "subtitle": "Một không gian truy cập nhanh mọi chức năng của AETHERION.",
        "overview": "Tổng quan",
        "workspace": "WORKSPACE  /  OPERATIONS",
        "navigator": "ĐIỀU HƯỚNG",
        "sources": "KHOA HỌC & NGUỒN",
        "clinical": "SỨC KHỎE",
        "systems": "HỆ THỐNG",
        "mission": "Điều hành",
        "health": "Sức khỏe của tôi",
        "monitor": "Theo dõi",
        "ecg": "Điện tim (ECG)",
        "assistant": "Hỏi AI",
        "interview": "Đánh giá triệu chứng",
        "care": "Hành trình chăm sóc",
        "science": "Khám phá khoa học",
        "hazards": "Nguy cơ bay vũ trụ",
        "medical_library": "Thư viện y khoa",
        "atlas": "Cơ thể 3D",
        "crew": "Phi hành đoàn",
        "settings": "Cài đặt",
        "demo.title": "DEMO FOR HACKATHON",
        "demo.subtitle": "Kịch bản minh họa giả lập · hồ sơ độc lập",
        "demo.badge": "SIMULATED · DỮ LIỆU GIẢ LẬP",
        "demo.detail": "Mở phần giới thiệu trước khi đi vào kịch bản giả lập. Không ghi vào bệnh án hoặc dữ liệu phi hành đoàn thật.",
        "demo.action": "Bắt đầu Demo",
        "briefing.badge": "SIMULATED · KHÔNG PHẢI BỆNH ÁN",
        "briefing.title": "Kịch bản hồ sơ giả lập",
        "briefing.copy": "Khám phá bộ dữ liệu ngoại tuyến để thử trải nghiệm. Mọi người, giá trị và xu hướng đều hư cấu; đây không phải phép đo, chẩn đoán hay dữ liệu NASA.",
        "briefing.dataset": "5 hồ sơ hư cấu · 540 ngày · 12 nhóm chỉ số",
        "briefing.storage": "Dữ liệu nằm trong SQLite Demo riêng. Không ghi vào hồ sơ sức khỏe đã xác thực hoặc kho NASA.",
        "briefing.provenance": "Nguồn: AETHERION-SYNTHETIC-PATIENTS-V1 · TEST_FIXTURE · UNVERIFIED",
        "briefing.start": "Nạp dữ liệu giả lập",
        "briefing.back": "Về Trung tâm điều hành",
        "nasa.title": "NASA · MA-7",
        "nasa.subtitle": "83 giá trị đo NASA công bố năm 1962",
        "nasa.badge": "HISTORICAL SOURCE · KHÔNG TRỰC TIẾP",
        "nasa.detail": "Dữ liệu lịch sử thật có nguồn NASA, tách khỏi kịch bản SIMULATED.",
        "nasa.action": "Khám phá NASA",
        "overview.title": "Một trung tâm. Mọi chức năng.",
        "overview.copy": "Chọn một mục từ cây điều hướng hoặc khu thao tác. Những chức năng chưa có dữ liệu sẽ tự báo tình trạng từ màn hình tương ứng.",
        "data.title": "TÍNH TOÀN VẸN NGUỒN",
        "data.health": "Dữ liệu sức khỏe",
        "data.healthState": "Chỉ hiển thị khi được cấp quyền",
        "data.science": "Nguồn NASA",
        "data.scienceState": "Tài liệu tham khảo · không phải hồ sơ sống",
        "data.demo": "Kịch bản Demo",
        "data.demoState": "Giả lập · không kết nối người bệnh",
        "quick.title": "MỞ NHANH",
        "quick.copy": "Toàn bộ mô-đun được truy cập qua một thanh điều hướng. Không cần quay về màn hình năm thẻ.",
        "status.label": "TRẠNG THÁI",
        "status.unknown": "Chưa kiểm tra kết nối",
        "context": "NGUỒN VÀ GIỚI HẠN",
        "context.title": "Dữ liệu có nguồn.",
        "context.copy": "Không có chỉ số bệnh nhân hay tín hiệu thời gian thực giả trên màn hình điều hành. Xem từng ứng dụng để kiểm tra dữ liệu đã xác thực.",
        "context.source": "NASA MA-7: số liệu nghiên cứu lịch sử thật",
        "context.scenario": "Hackathon Demo: nguồn giả lập được ghi nhãn",
        "context.privacy": "Hồ sơ sức khỏe: yêu cầu xác thực và phân quyền",
        "context.link": "Mở kho NASA",
        "footer": "NATIVE DESKTOP  /  LOCAL-FIRST  /  RESEARCH-AWARE",
        "open": "Mở {title}",
    },
    "en": {
        "eyebrow": "TRUY TINH  /  MISSION OPERATIONS",
        "title": "Mission Control",
        "subtitle": "One command workspace for every AETHERION feature.",
        "overview": "Overview",
        "workspace": "WORKSPACE  /  OPERATIONS",
        "navigator": "NAVIGATION",
        "sources": "SCIENCE & SOURCES",
        "clinical": "HEALTH",
        "systems": "SYSTEMS",
        "mission": "Operations",
        "health": "My Health",
        "monitor": "Monitoring",
        "ecg": "ECG",
        "assistant": "Ask AI",
        "interview": "Symptom Interview",
        "care": "Care Journey",
        "science": "Explore Science",
        "hazards": "Spaceflight Hazards",
        "medical_library": "Medical Library",
        "atlas": "Body Atlas",
        "crew": "Crew",
        "settings": "Settings",
        "demo.title": "DEMO FOR HACKATHON",
        "demo.subtitle": "Clearly simulated scenario · isolated profiles",
        "demo.badge": "SIMULATED · FICTIONAL DATA",
        "demo.detail": "Read the scenario explanation before entering the fictional environment. Never writes into real crew or patient records.",
        "demo.action": "Start Demo",
        "briefing.badge": "SIMULATED · NOT PATIENT DATA",
        "briefing.title": "Synthetic patient scenario",
        "briefing.copy": "Explore an offline usability dataset. Every person, value, and trend is fictional; these are not measurements, diagnoses, or NASA data.",
        "briefing.dataset": "5 fictional profiles · 540 days · 12 metric families",
        "briefing.storage": "Stored in a separate Demo SQLite database. Nothing is written to authenticated health records or the NASA archive.",
        "briefing.provenance": "Source: AETHERION-SYNTHETIC-PATIENTS-V1 · TEST_FIXTURE · UNVERIFIED",
        "briefing.start": "Load simulated data",
        "briefing.back": "Back to Mission Operations",
        "nasa.title": "NASA · MA-7",
        "nasa.subtitle": "83 actual published NASA values from 1962",
        "nasa.badge": "HISTORICAL SOURCE · NOT LIVE",
        "nasa.detail": "Real, NASA-cited historical research, kept separate from the SIMULATED scenario.",
        "nasa.action": "Explore NASA",
        "overview.title": "One command center. Every capability.",
        "overview.copy": "Select a module in the navigator or a quick action. Unavailable data must be disclosed in the target screen.",
        "data.title": "SOURCE INTEGRITY",
        "data.health": "Health records",
        "data.healthState": "Visible only to authorized users",
        "data.science": "NASA sources",
        "data.scienceState": "Research references · not live records",
        "data.demo": "Demo scenario",
        "data.demoState": "Fictional · disconnected from patients",
        "quick.title": "QUICK ACCESS",
        "quick.copy": "All modules live in one navigator; no oversized five-card landing screen.",
        "status.label": "STATUS",
        "status.unknown": "Connection not verified",
        "context": "SOURCES & LIMITATIONS",
        "context.title": "Evidence before claims.",
        "context.copy": "No fabricated patient vitals or live signals are shown in Mission Control. Open a specific screen to inspect authenticated data.",
        "context.source": "NASA MA-7: real historical research measurements",
        "context.scenario": "Hackathon Demo: explicitly fictional scenario",
        "context.privacy": "Health records: authentication and authorization required",
        "context.link": "Open NASA research",
        "footer": "NATIVE DESKTOP  /  LOCAL-FIRST  /  RESEARCH-AWARE",
        "open": "Open {title}",
    },
}


def _locale(raw: str) -> str:
    return "en" if str(raw).lower().startswith("en") else "vi"


class OrbitPanel(QFrame):
    """Procedural visual ornament, NOT a spacecraft sensor or body model."""

    def __init__(self, parent=None, *, reduce_motion=False):
        super().__init__(parent)
        self.setObjectName("contentPanel")
        self.setMinimumHeight(140)
        self.phase = 0.0
        self.reduce_motion = bool(reduce_motion)
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._step)

    def showEvent(self, event):
        super().showEvent(event)
        self._animate()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def set_motion(self, reduced: bool):
        self.reduce_motion = bool(reduced)
        self._animate()
        self.update()

    def _animate(self):
        if self.isVisible() and not self.reduce_motion:
            self.timer.start()
        else:
            self.timer.stop()

    def _step(self):
        self.phase = (self.phase + 0.004) % 1.0
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        x, y = w * .75, h * .52
        painter.translate(x, y)
        light = QRadialGradient(0, 0, min(170, w * .2))
        light.setColorAt(0, QColor(92, 156, 222, 78))
        light.setColorAt(1, QColor(92, 156, 222, 0))
        painter.setBrush(light)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(-155, -155, 310, 310))
        for index, r in enumerate((42, 67, 96)):
            c = QColor(112, 197, 226, 118 - index * 24)
            painter.setPen(QPen(c, 1.2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(-r, -r * .5, r * 2, r))
            theta = (self.phase * math.tau + index * 2.2)
            px, py = r * math.cos(theta), r * .5 * math.sin(theta)
            painter.setBrush(QColor(178, 238, 255, 200))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(px - 3, py - 3, 6, 6))
        painter.end()


class MissionOperationsHome(QWidget):
    """Composition-only desktop Home; host must attach real route handlers."""

    route_requested = Signal(str)
    simulated_demo_requested = Signal()
    nasa_archive_requested = Signal()

    def __init__(self, parent=None, *, locale="en", reduce_motion=False):
        super().__init__(parent)
        self.language = _locale(locale)
        self.reduce_motion = bool(reduce_motion)
        self.setObjectName("missionOperationsHome")
        self._route_items = {}
        self._action_buttons = {}
        self._source_state = "unknown"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(17, 12, 17, 12)
        layout.setSpacing(11)

        heading = QFrame()
        heading.setObjectName("surface")
        header = QHBoxLayout(heading)
        header.setContentsMargins(18, 10, 18, 10)
        self.brand = QLabel()
        self.brand.setObjectName("eyebrow")
        header.addWidget(self.brand, 1)
        self.health_status = QLabel()
        self.health_status.setObjectName("connectionPill")
        header.addWidget(self.health_status)
        self.primary_demo = QPushButton()
        self.primary_demo.setObjectName("primaryAction")
        self.primary_demo.setMinimumHeight(39)
        self.primary_demo.clicked.connect(self.simulated_demo_requested.emit)
        header.addWidget(self.primary_demo)
        layout.addWidget(heading)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setChildrenCollapsible(False)
        split.setHandleWidth(5)
        self.navigator = QTreeWidget()
        self.navigator.setObjectName("opsNavigator")
        self.navigator.setHeaderHidden(True)
        self.navigator.setMinimumWidth(190)
        self.navigator.setMaximumWidth(265)
        self.navigator.setUniformRowHeights(True)
        self.navigator.itemClicked.connect(self._navigate)
        split.addWidget(self.navigator)

        center_container = QWidget()
        center_container.setObjectName("opsContent")
        center_outer = QVBoxLayout(center_container)
        center_outer.setContentsMargins(0, 0, 0, 0)
        self.center_scroll = QScrollArea()
        self.center_scroll.setWidgetResizable(True)
        self.center_scroll.setFrameShape(QFrame.Shape.NoFrame)
        center_outer.addWidget(self.center_scroll)
        center = QWidget()
        self.center_scroll.setWidget(center)
        content = QVBoxLayout(center)
        content.setContentsMargins(13, 7, 13, 10)
        content.setSpacing(14)

        self.canvas = OrbitPanel(reduce_motion=reduce_motion)
        canvas_layout = QVBoxLayout(self.canvas)
        canvas_layout.setContentsMargins(23, 15, 180, 16)
        canvas_layout.setSpacing(5)
        self.canvas_eyebrow = QLabel()
        self.canvas_eyebrow.setObjectName("eyebrow")
        canvas_layout.addWidget(self.canvas_eyebrow)
        self.main_title = QLabel()
        self.main_title.setObjectName("heroTitle")
        self.main_title.setWordWrap(True)
        canvas_layout.addWidget(self.main_title)
        self.main_subtitle = QLabel()
        self.main_subtitle.setObjectName("heroCopy")
        self.main_subtitle.setWordWrap(True)
        canvas_layout.addWidget(self.main_subtitle)
        content.addWidget(self.canvas)

        actions = QGridLayout()
        actions.setHorizontalSpacing(13)
        actions.setVerticalSpacing(12)
        for col, key in enumerate(("simulated", "nasa")):
            card = QFrame()
            card.setObjectName("contentPanel")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(17, 14, 17, 14)
            card_layout.setSpacing(7)
            badge = QLabel()
            badge.setObjectName("eyebrow")
            card_layout.addWidget(badge)
            title = QLabel()
            title.setObjectName("heading")
            title.setWordWrap(True)
            card_layout.addWidget(title)
            subtitle = QLabel()
            subtitle.setObjectName("pageHint")
            subtitle.setWordWrap(True)
            card_layout.addWidget(subtitle)
            detail = QLabel()
            detail.setObjectName("pageHint")
            detail.setWordWrap(True)
            card_layout.addWidget(detail)
            action = QPushButton()
            action.setObjectName("primaryAction" if key == "simulated" else "navButton")
            action.setMinimumHeight(38)
            if key == "simulated":
                action.clicked.connect(self.simulated_demo_requested.emit)
            else:
                action.clicked.connect(self.nasa_archive_requested.emit)
            card_layout.addWidget(action)
            actions.addWidget(card, 0, col)
            self._action_buttons[key] = (badge, title, subtitle, detail, action)
        content.addLayout(actions)

        section = QFrame()
        section.setObjectName("contentPanel")
        block = QVBoxLayout(section)
        block.setContentsMargins(18, 14, 18, 15)
        self.integrity_title = QLabel()
        self.integrity_title.setObjectName("eyebrow")
        block.addWidget(self.integrity_title)
        self.safety_lines = []
        for _ in range(3):
            line = QLabel()
            line.setObjectName("pageHint")
            line.setWordWrap(True)
            block.addWidget(line)
            self.safety_lines.append(line)
        content.addWidget(section)
        self.quick_heading = QLabel()
        self.quick_heading.setObjectName("eyebrow")
        content.addWidget(self.quick_heading)
        quick_grid = QGridLayout()
        self.quick_routes = ("health", "monitor", "assistant", "interview",
                             "care", "science", "ecg", "crew")
        self.quick_buttons = {}
        for i, route in enumerate(self.quick_routes):
            button = QPushButton()
            button.setObjectName("navButton")
            button.clicked.connect(lambda checked=False, key=route:
                                   self.route_requested.emit(key))
            quick_grid.addWidget(button, i // 4, i % 4)
            self.quick_buttons[route] = button
        content.addLayout(quick_grid)
        content.addStretch(1)
        split.addWidget(center_container)

        context = QFrame()
        context.setObjectName("contentPanel")
        context.setMinimumWidth(185)
        context.setMaximumWidth(255)
        context_layout = QVBoxLayout(context)
        context_layout.setContentsMargins(14, 16, 14, 16)
        context_layout.setSpacing(9)
        self.context_title = QLabel()
        self.context_title.setObjectName("eyebrow")
        context_layout.addWidget(self.context_title)
        self.context_heading = QLabel()
        self.context_heading.setObjectName("heading")
        self.context_heading.setWordWrap(True)
        context_layout.addWidget(self.context_heading)
        self.context_detail = QLabel()
        self.context_detail.setObjectName("pageHint")
        self.context_detail.setWordWrap(True)
        context_layout.addWidget(self.context_detail)
        self.context_items = []
        for _ in range(3):
            label = QLabel()
            label.setObjectName("pageHint")
            label.setWordWrap(True)
            context_layout.addWidget(label)
            self.context_items.append(label)
        context_layout.addStretch(1)
        self.science_action = QPushButton()
        self.science_action.setObjectName("navButton")
        self.science_action.clicked.connect(lambda: self.route_requested.emit("science"))
        context_layout.addWidget(self.science_action)
        self.context_panel = context
        split.addWidget(context)
        split.setSizes([235, 870, 230])
        layout.addWidget(split, 1)
        self.splitter = split
        self.footer = QLabel()
        self.footer.setObjectName("pageHint")
        layout.addWidget(self.footer)

        self.set_locale(locale)
        self._size_context()

    def _t(self, key, **fields):
        text = TEXT[self.language][key]
        return text.format(**fields) if fields else text

    def set_locale(self, raw):
        self.language = _locale(raw)
        self.brand.setText(self._t("eyebrow"))
        self.canvas_eyebrow.setText(self._t("workspace"))
        self.main_title.setText(self._t("title"))
        self.main_subtitle.setText(self._t("subtitle"))
        self.health_status.setText(self._t("status.unknown"))
        self.primary_demo.setText(self._t("demo.title"))
        self.primary_demo.setAccessibleName(self._t("demo.badge"))
        self.integrity_title.setText(self._t("data.title"))
        self.quick_heading.setText(self._t("quick.title"))
        self.footer.setText(self._t("footer"))
        for name, row in self._action_buttons.items():
            prefix = "demo" if name == "simulated" else "nasa"
            for label, key in zip(row, ("badge", "title", "subtitle", "detail", "action")):
                label.setText(self._t(prefix + "." + key))
            row[4].setAccessibleName(self._t(prefix + ".title"))
        for label, key in zip(self.safety_lines, ("health", "science", "demo")):
            label.setText(self._t("data."+key) + "   /   " + self._t("data."+key+"State"))
        for key, button in self.quick_buttons.items():
            button.setText(self._t(key))
            button.setAccessibleName(self._t("open", title=self._t(key)))
        self.context_title.setText(self._t("context"))
        self.context_heading.setText(self._t("context.title"))
        self.context_detail.setText(self._t("context.copy"))
        for label, key in zip(self.context_items, ("context.source", "context.scenario", "context.privacy")):
            label.setText("• " + self._t(key))
        self.science_action.setText(self._t("context.link"))
        self._fill_navigator()

    def _fill_navigator(self):
        self.navigator.blockSignals(True)
        self.navigator.clear()
        self._route_items.clear()
        categories = (
            ("navigator", ("mission", "crew")),
            ("clinical", ("health", "monitor", "ecg", "assistant", "interview", "care")),
            ("sources", ("science", "hazards", "medical_library", "atlas")),
            ("systems", ("settings",)),
        )
        for category, routes in categories:
            parent = QTreeWidgetItem([self._t(category)])
            parent.setFlags(parent.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.navigator.addTopLevelItem(parent)
            for route in routes:
                item = QTreeWidgetItem([self._t(route)])
                item.setData(0, Qt.ItemDataRole.UserRole, route)
                parent.addChild(item)
                self._route_items[route] = item
            parent.setExpanded(True)
        self.navigator.blockSignals(False)
        self.navigator.setAccessibleName(self._t("navigator"))

    def _navigate(self, item, _column):
        route = item.data(0, Qt.ItemDataRole.UserRole)
        if isinstance(route, str) and route in ROUTE_IDS:
            self.route_requested.emit(route)

    def set_visuals(self, theme=None, reduce_motion=False, mode=None, intensity=48):
        """Theme styles are inherited from host app; no owner theme override."""
        self.reduce_motion = bool(reduce_motion)
        self.canvas.set_motion(self.reduce_motion)

    def set_connection_state(self, state):
        # Never infer connectivity from demo availability.
        self._source_state = str(state)
        # Callers must source state from a successful real /health request.
        self.health_status.setText(self._source_state if self._source_state != "unknown"
                                   else self._t("status.unknown"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._size_context()

    def _size_context(self):
        if hasattr(self, "context_panel"):
            self.context_panel.setVisible(self.width() >= 1210)


class SimulatedDemoBriefing(QWidget):
    """Clear source and privacy boundary shown before synthetic data is loaded."""

    start_requested = Signal()
    back_requested = Signal()

    def __init__(self, parent=None, *, locale="en"):
        super().__init__(parent)
        self.setObjectName("simulatedDemoBriefing")
        self.language = _locale(locale)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 25)
        layout.setSpacing(14)

        self.back_button = QPushButton()
        self.back_button.setObjectName("navButton")
        self.back_button.clicked.connect(self.back_requested.emit)
        layout.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)

        self.card = QFrame()
        self.card.setObjectName("contentPanel")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(24, 22, 24, 24)
        card_layout.setSpacing(12)
        self.badge = QLabel()
        self.badge.setObjectName("connectionPill")
        card_layout.addWidget(self.badge, 0, Qt.AlignmentFlag.AlignLeft)
        self.title = QLabel()
        self.title.setObjectName("heroTitle")
        self.title.setWordWrap(True)
        card_layout.addWidget(self.title)
        self.description = QLabel()
        self.description.setObjectName("heroCopy")
        self.description.setWordWrap(True)
        card_layout.addWidget(self.description)
        self.dataset = QLabel()
        self.dataset.setObjectName("heading")
        self.dataset.setWordWrap(True)
        card_layout.addWidget(self.dataset)
        self.storage = QLabel()
        self.storage.setObjectName("pageHint")
        self.storage.setWordWrap(True)
        card_layout.addWidget(self.storage)
        self.provenance = QLabel()
        self.provenance.setObjectName("pageHint")
        self.provenance.setWordWrap(True)
        card_layout.addWidget(self.provenance)
        self.start_button = QPushButton()
        self.start_button.setObjectName("primaryAction")
        self.start_button.setMinimumHeight(46)
        self.start_button.clicked.connect(self.start_requested.emit)
        card_layout.addWidget(self.start_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.card)
        layout.addStretch(1)
        self.set_locale(self.language)

    def _t(self, key):
        return TEXT[self.language]["briefing." + key]

    def set_locale(self, raw):
        self.language = _locale(raw)
        self.badge.setText(self._t("badge"))
        self.badge.setAccessibleName(self._t("badge"))
        self.title.setText(self._t("title"))
        self.description.setText(self._t("copy"))
        self.dataset.setText(self._t("dataset"))
        self.storage.setText(self._t("storage"))
        self.provenance.setText(self._t("provenance"))
        self.start_button.setText(self._t("start"))
        self.start_button.setAccessibleName(self._t("start"))
        self.back_button.setText(self._t("back"))
        self.back_button.setAccessibleName(self._t("back"))

    def set_visuals(self, theme=None, reduce_motion=False, mode=None, intensity=48):
        """Inherit the host application's palette; briefing has no animation."""


def build_mission_ops_home(parent=None, **kwargs):
    return MissionOperationsHome(parent, **kwargs)


def build_simulated_demo_briefing(parent=None, *, locale="en"):
    return SimulatedDemoBriefing(parent, locale=locale)
