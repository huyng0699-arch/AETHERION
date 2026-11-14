"""AETHERION native Windows app — Portal-first premium Qt shell.

AETHERION Server remains the single source of data. The client never invents
sensor readings, AI answers, anatomy, or an emergency dispatch service.
"""
from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QAction, QShortcut, QKeySequence
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMessageBox, QPushButton, QSizePolicy, QStackedWidget, QToolButton,
    QVBoxLayout, QWidget,
)

from .portal import PORTAL_ROUTES, build_portal_page
from .localization import normalize_locale, tr, translate_existing, translate_shell_widgets
from .visual_theme import THEMES, VisualPreferences
from .settings_page import SettingsPage
from .localize import tr as settings_tr
from .medical_library import build_medical_library_page
from .mission_control import build_mission_control_page
from .features.personal.authorized_today import AuthorizedPersonalTodayPage
from .features.explore.nasa_explore import build_nasa_explore_page


class FeatureLanding(QWidget):
    """Honest native entry for work that is not yet connected to a real source."""

    def __init__(self, eyebrow: str, title: str, description: str, actions=(), parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(55, 49, 55, 40)
        root.setSpacing(14)
        code = QLabel(eyebrow.upper())
        code.setObjectName("eyebrow")
        root.addWidget(code)
        heading = QLabel(title)
        heading.setObjectName("heading")
        root.addWidget(heading)
        explanation = QLabel(description)
        explanation.setObjectName("heroCopy")
        explanation.setWordWrap(True)
        root.addWidget(explanation)
        panel = QFrame()
        panel.setObjectName("contentPanel")
        block = QVBoxLayout(panel)
        block.setContentsMargins(26, 25, 26, 26)
        block.setSpacing(14)
        status = QLabel("CHƯA CÓ DỮ LIỆU / CHƯA KẾT NỐI TÍNH NĂNG")
        status.setObjectName("eyebrow")
        block.addWidget(status)
        hint = QLabel("Chỉ dữ liệu thật, có nguồn xác định và quyền truy cập hợp lệ mới được hiển thị.")
        hint.setObjectName("pageHint")
        hint.setWordWrap(True)
        block.addWidget(hint)
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        for index, (label, handler) in enumerate(actions):
            btn = QPushButton(label)
            btn.setObjectName("primaryAction" if index == 0 else "navButton")
            btn.clicked.connect(handler)
            buttons.addWidget(btn)
        buttons.addStretch()
        block.addLayout(buttons)
        root.addWidget(panel)
        root.addStretch()


class AetherionWindow(QMainWindow):
    """One top menu, a native five-card Home, and existing authenticated views."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AETHERION  ·  TRUY TINH")
        self.resize(1360, 850)
        self.setMinimumSize(1040, 650)
        self.api_url = os.environ.get("AETHERION_API_URL", "http://127.0.0.1:8765").rstrip("/")
        self.network = QNetworkAccessManager(self)
        self.preferences = VisualPreferences()
        self.ui_language = normalize_locale(self.preferences.settings.value("ui/language", "vi"))
        app = QApplication.instance()
        if app is not None:
            self.preferences.apply(app)

        root = QWidget()
        root.setObjectName("appRoot")
        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        top = QFrame()
        top.setObjectName("topBar")
        self.top_bar = top
        bar = QHBoxLayout(top)
        bar.setContentsMargins(25, 10, 25, 10)
        bar.setSpacing(9)
        brand = QPushButton("◈  AETHERION")
        brand.setObjectName("brandButton")
        brand.setAccessibleName("AETHERION — về Trang đầu")
        brand.clicked.connect(self.show_portal)
        bar.addWidget(brand)
        bar.addSpacing(14)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageStack")
        self.portal_page = build_portal_page(theme_name=self.preferences.theme_name,
                                             reduce_motion=self.preferences.reduce_motion,
                                             locale=self.ui_language,
                                             mode=self.preferences.mode,
                                             intensity=self.preferences.animation_intensity)
        self.portal_page.route_requested.connect(self.open_portal_route)
        self.portal_page.theme_requested.connect(self.show_settings)
        self.pages.addWidget(self.portal_page)

        # Preserve real, already implemented features and their authenticated links.
        self.mission_control_page = build_mission_control_page(self.api_url, self.network)
        self.pages.addWidget(self.mission_control_page)
        self.personal_today_page = AuthorizedPersonalTodayPage(self.api_url, self.network)
        self.pages.addWidget(self.personal_today_page)
        self.medical_library_page = build_medical_library_page()
        self.pages.addWidget(self.medical_library_page)
        self.nasa_explore_page = build_nasa_explore_page()
        self.pages.addWidget(self.nasa_explore_page)
        self.mission_control_page.subject_activated.connect(self.open_personal_subject)

        self.monitor_page = FeatureLanding(
            "02 / MEASUREMENTS", "Theo dõi & ECG",
            "Hồ sơ đo lường cần một nguồn thật đã được ghép và cấp quyền. "
            "ECG không có dạng sóng trước khi nhập bản ghi hợp lệ.",
            (("Xem dữ liệu đang lưu", self.show_mission), ("Thư viện y khoa", self.show_medical_library)),
        )
        self.pages.addWidget(self.monitor_page)
        self.assistant_page = FeatureLanding(
            "03 / INTELLIGENCE", "Hỏi AI về sức khỏe",
            "Trợ lý AI Local/Cloud chưa được xác nhận hoạt động trên Server. "
            "Trong lúc này, bạn có thể đọc thư viện đã nhập và kiểm chứng nguồn.",
            (("Mở thư viện khoa học", self.show_medical_library),),
        )
        self.pages.addWidget(self.assistant_page)
        self.atlas_page = FeatureLanding(
            "04 / DISCOVERY", "Khám phá cơ thể",
            "Mô hình giải phẫu 3D chỉ được mở khi có mesh thật, camera và chọn vùng cơ thể. "
            "Hình động nền không phải Atlas 3D.",
            (("Tìm hiểu tài liệu", self.show_medical_library),),
        )
        self.pages.addWidget(self.atlas_page)
        self.care_page = FeatureLanding(
            "05 / CONTINUITY", "Hành trình chăm sóc",
            "Quy trình Thu thập → Đánh giá → Hành động → Kiểm tra lại cần "
            "lưu trên Server và tuân theo quy tắc chuyên môn được kiểm chứng.",
            (("Mở Sức khỏe của tôi", self.show_personal),),
        )
        self.pages.addWidget(self.care_page)
        self.settings_page = SettingsPage(self.preferences, self.api_url)
        self.settings_page.preferences_changed.connect(self._apply_preferences)
        self.settings_page.connection_test_requested.connect(self.check_server)
        self.settings_page.go_home.connect(self.show_portal)
        self.pages.addWidget(self.settings_page)

        # Main horizontal navigation; nested items use dropdown menus, never sidebars.
        self._nav_button(bar, "Trang đầu", self.show_portal)
        self._nav_menu(bar, "Sức khỏe ▾", (
            ("Sức khỏe hôm nay", self.show_personal),
            ("Hành trình chăm sóc", self.show_care),
        ))
        self._nav_menu(bar, "Theo dõi ▾", (
            ("Tổng quan đo lường", self.show_monitor),
            ("Điện tim (ECG)", self.show_monitor),
            ("Bản ghi được cấp quyền", self.show_mission),
        ))
        self._nav_button(bar, "Hỏi AI", self.show_assistant)
        self._nav_menu(bar, "Khám phá ▾", (
            ("NASA Explore · Năm nguy cơ", self.show_nasa_explore),
            ("Thư viện y khoa", self.show_medical_library),
            ("Cơ thể 3D", self.show_atlas),
        ))
        self._nav_button(bar, "Phi hành đoàn", self.show_mission)
        bar.addStretch(1)

        self.status = QLabel("○  Đang kiểm tra")
        self.status.setObjectName("connectionPill")
        self.status.setToolTip("Trạng thái HTTP Server tại địa chỉ cấu hình")
        bar.addWidget(self.status)
        self.theme_button = QToolButton()
        self.theme_button.setText("◐  Giao diện")
        self.theme_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.theme_button.setAccessibleName("Thay đổi chủ đề, cỡ chữ và giảm chuyển động")
        self.theme_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.theme_menu = QMenu(self.theme_button)
        self.theme_button.setMenu(self.theme_menu)
        self._build_theme_menu()
        self.theme_menu.aboutToShow.connect(self._build_theme_menu)
        bar.addWidget(self.theme_button)
        # Locale is UI-only and persists locally; it never touches health records.
        self.language_button = QToolButton()
        self.language_button.setObjectName("languageButton")
        self.language_button.setToolTip(tr(self.ui_language, "main.locale.tooltip"))
        self.language_button.clicked.connect(self._change_language)
        bar.addWidget(self.language_button)
        self.settings_button = QPushButton("⚙  "+settings_tr("settings",self.ui_language))
        self.settings_button.setObjectName("navButton")
        self.settings_button.setAccessibleName("AETHERION Settings")
        self.settings_button.clicked.connect(self.show_settings)
        bar.addWidget(self.settings_button)
        help_button = QToolButton()
        help_button.setText("?  Trợ giúp")
        help_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        help_button.clicked.connect(self.show_help)
        bar.addWidget(help_button)
        outer.addWidget(top)
        outer.addWidget(self.pages, 1)

        footer = QFrame()
        footer.setObjectName("footerBar")
        self.footer_bar = footer
        line = QHBoxLayout(footer)
        line.setContentsMargins(28, 6, 28, 6)
        left = QLabel("TRUY TINH  /  INDEPENDENT HEALTH INTELLIGENCE")
        left.setObjectName("pageHint")
        line.addWidget(left)
        line.addStretch()
        right = QLabel("Không phải thiết bị y tế · Chỉ hiện dữ liệu đã được xác minh nguồn")
        right.setObjectName("pageHint")
        line.addWidget(right)
        outer.addWidget(footer)

        self.setCentralWidget(root)
        self.shortcut_settings = QShortcut(QKeySequence("Ctrl+,"), self)
        self.shortcut_settings.activated.connect(self.show_settings)
        self.shortcut_home = QShortcut(QKeySequence("Alt+Home"), self)
        self.shortcut_home.activated.connect(self.show_portal)
        self._retranslate_shell()
        self.pages.setCurrentWidget(self.portal_page)
        self.heartbeat = QTimer(self)
        self.heartbeat.setInterval(30000)
        self.heartbeat.timeout.connect(self.check_server)
        self.heartbeat.start()

    @staticmethod
    def _nav_button(layout, text, handler):
        button = QPushButton(text)
        button.setObjectName("navButton")
        button.setMinimumHeight(38)
        button.clicked.connect(handler)
        layout.addWidget(button)
        return button

    @staticmethod
    def _nav_menu(layout, text, actions):
        button = QToolButton()
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        menu = QMenu(button)
        for label, handler in actions:
            entry = QAction(label, menu)
            entry.triggered.connect(handler)
            menu.addAction(entry)
        button.setMenu(menu)
        layout.addWidget(button)
        return button

    def _build_theme_menu(self):
        self.theme_menu.clear()
        for code, theme in THEMES.items():
            action = QAction(translate_existing(theme.title, self.ui_language), self.theme_menu)
            action.setCheckable(True)
            action.setChecked(code == self.preferences.theme_name)
            action.triggered.connect(lambda checked=False, key=code: self._change_theme(key))
            self.theme_menu.addAction(action)
        self.theme_menu.addSeparator()
        motion = QAction(tr(self.ui_language, "main.theme.motion"), self.theme_menu)
        motion.setCheckable(True)
        motion.setChecked(self.preferences.reduce_motion)
        motion.triggered.connect(self._change_motion)
        self.theme_menu.addAction(motion)
        self.theme_menu.addSeparator()
        smaller = QAction(tr(self.ui_language, "main.theme.smaller"), self.theme_menu)
        smaller.triggered.connect(lambda: self._change_font(-1))
        larger = QAction(tr(self.ui_language, "main.theme.larger"), self.theme_menu)
        larger.triggered.connect(lambda: self._change_font(1))
        self.theme_menu.addAction(smaller)
        self.theme_menu.addAction(larger)

    def _retranslate_shell(self):
        """Retitle the localized shell without rewriting NASA/clinical content."""
        self.portal_page.set_locale(self.ui_language)
        for section in (
            self.top_bar, self.monitor_page, self.assistant_page,
            self.atlas_page, self.care_page, self.footer_bar,
        ):
            translate_shell_widgets(section, self.ui_language)
        self.language_button.setText(f"VI / EN · {self.ui_language.upper()}")
        self.language_button.setToolTip(tr(self.ui_language, "main.locale.tooltip"))
        self.language_button.setAccessibleName(tr(self.ui_language, "main.locale.tooltip"))
        self._build_theme_menu()
        self.settings_button.setText("⚙  "+settings_tr("settings",self.ui_language))
        self.check_server()

    def _change_language(self):
        self.ui_language = "en" if self.ui_language == "vi" else "vi"
        self.preferences.set_language(self.ui_language)
        self._retranslate_shell()
        self.settings_page.retranslate()

    def _change_theme(self, theme_name: str):
        self.preferences.set_theme(theme_name)
        self._apply_preferences()

    def _change_motion(self, checked: bool):
        self.preferences.set_reduced_motion(checked)
        self._apply_preferences()

    def _change_font(self, delta: int):
        self.preferences.set_font_size(self.preferences.font_size + delta)
        self._apply_preferences()

    def _apply_preferences(self):
        app = QApplication.instance()
        if app is not None:
            self.preferences.apply(app)
        self.portal_page.set_visuals(
            self.preferences.theme_name, self.preferences.reduce_motion,
            self.preferences.mode, self.preferences.animation_intensity,
        )
        self.settings_page.retranslate()
        if self.ui_language != self.preferences.language:
            self.ui_language = self.preferences.language
            self._retranslate_shell()

    def open_theme_menu(self):
        self.show_settings()

    def show_settings(self):
        self.pages.setCurrentWidget(self.settings_page)

    def show_portal(self):
        self.pages.setCurrentWidget(self.portal_page)

    def show_personal(self):
        self.pages.setCurrentWidget(self.personal_today_page)

    def show_mission(self):
        self.pages.setCurrentWidget(self.mission_control_page)

    def show_medical_library(self):
        self.medical_library_page.reload()
        self.pages.setCurrentWidget(self.medical_library_page)

    def show_nasa_explore(self):
        self.nasa_explore_page.reload()
        self.pages.setCurrentWidget(self.nasa_explore_page)

    def show_monitor(self):
        self.pages.setCurrentWidget(self.monitor_page)

    def show_assistant(self):
        self.pages.setCurrentWidget(self.assistant_page)

    def show_atlas(self):
        self.pages.setCurrentWidget(self.atlas_page)

    def show_care(self):
        self.pages.setCurrentWidget(self.care_page)

    def open_portal_route(self, route: str):
        if route not in PORTAL_ROUTES:
            return
        {
            "health": self.show_personal,
            "monitor": self.show_monitor,
            "assistant": self.show_assistant,
            "science": self.show_nasa_explore,
            "crew": self.show_mission,
        }[route]()

    def open_personal_subject(self, subject_id: str, access_token: str):
        """Preserve the existing authorized Mission → Personal handoff."""
        self.personal_today_page.select_subject(subject_id, access_token)
        self.show_personal()

    def show_help(self):
        QMessageBox.information(
            self, tr(self.ui_language, "main.help.title"),
            tr(self.ui_language, "main.help.body"),
        )

    def check_server(self):
        self.status.setText(tr(self.ui_language, "main.status.checking"))
        request = QNetworkRequest(QUrl(self.api_url + "/health"))
        reply = self.network.get(request)
        reply.finished.connect(lambda: self.finish_check(reply))

    def finish_check(self, reply):
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = reply.error()
        body = bytes(reply.readAll()).decode("utf-8", errors="replace")
        if error != QNetworkReply.NetworkError.NoError or code != 200 or '"status":"ok"' not in body.replace(" ", ""):
            self.status.setText(tr(self.ui_language, "main.status.offline"))
            self.status.setToolTip(tr(self.ui_language, "main.status.offline.tooltip", url=self.api_url))
        else:
            self.status.setText(tr(self.ui_language, "main.status.online"))
            self.status.setToolTip(tr(self.ui_language, "main.status.online.tooltip", url=self.api_url))
        reply.deleteLater()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("AETHERION")
    app.setOrganizationName("TRUY TINH")
    window = AetherionWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
