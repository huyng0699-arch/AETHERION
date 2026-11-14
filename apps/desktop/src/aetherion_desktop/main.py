"""AETHERION native Windows app — Mission Operations-first Qt shell.

AETHERION Server remains the single source of data. The client never invents
sensor readings, AI answers, anatomy, or an emergency dispatch service.
"""
from __future__ import annotations

import os
import json
import sys

from PySide6.QtCore import Qt, QUrl, QTimer, QObject, QEvent
from PySide6.QtGui import QAction, QShortcut, QKeySequence
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu,
    QMessageBox, QPushButton, QSizePolicy, QStackedWidget, QToolButton,
    QVBoxLayout, QWidget,
)

from .login_page import LoginPage
from .portal import PORTAL_ROUTES, build_portal_page
from .mission_ops_home import build_mission_ops_home, ROUTE_IDS
from .features.demo.synthetic_briefing import SimulatedDemoBriefing
from .features.demo.synthetic_patient_ui import build_synthetic_patient_demo
from .startup_runtime import StartupRuntime
from .localization import normalize_locale, tr, translate_existing, translate_shell_widgets
from .visual_theme import THEMES, VisualPreferences, AmbientBackdrop
from .settings_page import SettingsPage
from .atlas3d import BodyAtlas3D
from .ecg_page import ECGPage
from .assistant_chat_page import ChatPage
from .native_workspaces import MonitoringWorkspace, InterviewWorkspace, CareWorkspace
from .localize import tr as settings_tr
from .medical_library import build_medical_library_page
from .mission_control import build_mission_control_page
from .features.personal.authorized_today import AuthorizedPersonalTodayPage
from .features.explore.nasa_explore import build_nasa_explore_page
from .knowledge_browser import KnowledgeBrowser
from .features.demo.nasa_ma7 import build_hackathon_demo
from .symptom_interview_page import SymptomInterviewPage
from .features.care.journey_page import CareJourneyPage


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


class PageAmbientController(QObject):
    """Subtle theme artwork beneath existing content; never alters measurements."""
    def __init__(self,parent=None):
        super().__init__(parent)
        self.layers={}
    def add_page(self,page,prefs):
        layer=AmbientBackdrop(page,prefs.theme_name,prefs.reduce_motion,
                              prefs.mode,min(24,prefs.animation_intensity))
        layer.setGeometry(page.rect())
        layer.lower()
        page.installEventFilter(self)
        self.layers[page]=layer
    def update_preferences(self,prefs):
        for layer in self.layers.values():
            layer.set_visuals(prefs.theme_name,prefs.reduce_motion,
                              prefs.mode,min(24,prefs.animation_intensity))
    def eventFilter(self,watched,event):
        if watched in self.layers and event.type()==QEvent.Type.Resize:
            layer=self.layers[watched]
            layer.setGeometry(watched.rect())
            layer.lower()
        return super().eventFilter(watched,event)


class AetherionWindow(QMainWindow):
    """One native mission-operations Home with existing authenticated views."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AETHERION  ·  TRUY TINH")
        self.resize(1360, 850)
        self.setMinimumSize(1040, 650)
        self.api_url = os.environ.get("AETHERION_API_URL", "http://127.0.0.1:8765").rstrip("/")
        self.network = QNetworkAccessManager(self)
        self.access_token = ""
        self.session_identity = None
        self.preferences = VisualPreferences()
        self.ui_language = normalize_locale(self.preferences.settings.value("ui/language", "en"))
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
        # Operations already owns the visible AETHERION identity and navigation.
        # The global bar contains appearance/language/settings/help only.
        self.brand_button = brand
        brand.hide()

        self.pages = QStackedWidget()
        self.pages.setObjectName("pageStack")
        self.login_page = LoginPage(self, network=self.network, api_url=self.api_url, locale=self.ui_language)
        self.login_page.authenticated.connect(self._login_complete)
        # Login Demo is the fictional crew walkthrough; genuine NASA archive
        # remains a separate, source-labelled route inside the briefing.
        self.login_page.demo_requested.connect(self.show_simulated_briefing)
        self.pages.addWidget(self.login_page)
        # Q-0485: first native view is mission operations, not the five-card Portal.
        self.operations_home_page = build_mission_ops_home(
            self, locale=self.ui_language,
            reduce_motion=self.preferences.reduce_motion,
        )
        self.operations_home_page.route_requested.connect(self.open_operations_route)
        self.operations_home_page.simulated_demo_requested.connect(self.show_simulated_briefing)
        self.operations_home_page.nasa_archive_requested.connect(self.show_hackathon_demo)
        self.pages.addWidget(self.operations_home_page)
        # Legacy Portal is retained for compatibility, never shown at cold launch.
        self.portal_page = build_portal_page(theme_name=self.preferences.theme_name,
                                             reduce_motion=self.preferences.reduce_motion,
                                             locale=self.ui_language,
                                             mode=self.preferences.mode,
                                             intensity=self.preferences.animation_intensity)
        self.portal_page.route_requested.connect(self.open_portal_route)
        self.portal_page.theme_requested.connect(self.show_settings)
        self.portal_page.demo_requested.connect(self.show_simulated_briefing)
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
        self.knowledge_browser_page = KnowledgeBrowser(
            self, api_url=self.api_url, locale=self.ui_language,
            theme=self.preferences.theme_name, mode=self.preferences.mode,
            reduce_motion=self.preferences.reduce_motion,
            intensity=self.preferences.animation_intensity,
        )
        self.pages.addWidget(self.knowledge_browser_page)
        self.hackathon_demo_page = build_hackathon_demo(
            self, locale=self.ui_language, theme=self.preferences.theme_name,
            mode=self.preferences.mode,
            reduce_motion=self.preferences.reduce_motion,
            intensity=self.preferences.animation_intensity,
        )
        self.hackathon_demo_page.home_requested.connect(self.show_portal)
        self.pages.addWidget(self.hackathon_demo_page)
        # SIMULATED patient experience is a separate widget, SQLite and identity
        # namespace. Start is called only by the explicit briefing CTA.
        self.simulated_briefing_page = SimulatedDemoBriefing(self, locale=self.ui_language)
        self.simulated_briefing_page.back_requested.connect(self.show_portal)
        self.simulated_briefing_page.start_requested.connect(self.start_simulated_demo)
        self.simulated_briefing_page.nasa_requested.connect(self.show_hackathon_demo)
        self.pages.addWidget(self.simulated_briefing_page)
        self.synthetic_patient_page = build_synthetic_patient_demo(
            self, locale=self.ui_language,
            theme=self.preferences.theme_name, mode=self.preferences.mode,
        )
        self.synthetic_patient_page.back_requested.connect(self.show_simulated_briefing)
        self.pages.addWidget(self.synthetic_patient_page)
        self.mission_control_page.subject_activated.connect(self.open_personal_subject)

        # Native, bilingual workspaces; only Server-backed records and questions.
        self.monitor_page = MonitoringWorkspace(self.api_url, self.network, self.ui_language)
        self.monitor_page.apply_theme(self.preferences)
        self.monitor_page.open_mission.connect(self.show_mission)
        self.pages.addWidget(self.monitor_page)
        self.ecg_page = ECGPage(self.api_url, self.network, self.ui_language)
        self.ecg_page.open_mission.connect(self.show_mission)
        self.pages.addWidget(self.ecg_page)
        self.assistant_page = ChatPage(self.api_url, self.network, self.ui_language)
        self.assistant_page.authorization_requested.connect(self.show_mission)
        self.assistant_page.open_symptom.connect(self.show_symptom_interview)
        self.assistant_page.open_library.connect(self.show_medical_library)
        self.pages.addWidget(self.assistant_page)
        self.symptom_page = SymptomInterviewPage(self, api_url=self.api_url, locale=self.ui_language)
        self.symptom_page.authorization_requested.connect(self.show_mission)
        self.symptom_page.care_created.connect(self._open_care_from_interview)
        self.pages.addWidget(self.symptom_page)
        self.atlas_page = BodyAtlas3D(api_url=self.api_url, network=self.network, locale=self.ui_language)
        self.pages.addWidget(self.atlas_page)
        self.care_page = CareWorkspace(self.ui_language)
        self.care_page.open_personal.connect(self.show_personal)
        self.care_page.open_monitor.connect(self.show_monitor)
        self.care_page.open_interview.connect(self.show_symptom_interview)
        self.pages.addWidget(self.care_page)
        self.care_journal_page = CareJourneyPage(self, api_url=self.api_url, locale=self.ui_language)
        self.pages.addWidget(self.care_journal_page)
        self.settings_page = SettingsPage(self.preferences, self.api_url)
        self.settings_page.preferences_changed.connect(self._apply_preferences)
        self.settings_page.connection_test_requested.connect(self.check_server)
        self.settings_page.go_home.connect(self.show_portal)
        self.pages.addWidget(self.settings_page)
        # Reparent the EXISTING native QWidget instances into the persistent
        # central mission-operations workspace. Q-0477/ECG/Chat logic, real API
        # permissions and signal connections are deliberately untouched.
        # QStackedWidget.removeWidget does not destroy widgets.
        for route, widget in (
            ("mission", self.mission_control_page),
            ("crew", self.mission_control_page),
            ("health", self.personal_today_page),
            ("monitor", self.monitor_page),
            ("ecg", self.ecg_page),
            ("assistant", self.assistant_page),
            ("interview", self.symptom_page),
            ("care", self.care_journal_page),
            ("science", self.knowledge_browser_page),
            ("hazards", self.nasa_explore_page),
            ("medical_library", self.medical_library_page),
            ("atlas", self.atlas_page),
            ("settings", self.settings_page),
            ("simulated_briefing", self.simulated_briefing_page),
            ("synthetic_patient", self.synthetic_patient_page),
            ("nasa_archive", self.hackathon_demo_page),
        ):
            if self.pages.indexOf(widget) >= 0:
                self.pages.removeWidget(widget)
            self.operations_home_page.attach_feature(route, widget)

        self.ambient_controller=PageAmbientController(self)
        for page in (self.mission_control_page,self.personal_today_page,
                     self.medical_library_page,self.nasa_explore_page,
                     self.knowledge_browser_page,self.hackathon_demo_page,
                     self.monitor_page,self.ecg_page,self.assistant_page,self.symptom_page,
                     self.atlas_page,self.care_page,self.care_journal_page):
            self.ambient_controller.add_page(page,self.preferences)

        # Existing global navigation coexists with the native Operations tree.
        self.nav_home = self._nav_button(bar, "Trang đầu", self.show_portal)
        self.nav_health = self._nav_menu(bar, "Sức khỏe ▾", (
            ("Sức khỏe hôm nay", self.show_personal),
            ("Hành trình chăm sóc", self.show_care),
        ))
        self.nav_monitor = self._nav_menu(bar, "Theo dõi ▾", (
            ("Tổng quan đo lường", self.show_monitor),
            ("Điện tim (ECG)", self.show_ecg),
            ("Bản ghi được cấp quyền", self.show_mission),
        ))
        self.nav_ai = self._nav_button(bar, "Hỏi AI", self.show_assistant)
        self.nav_science = self._nav_menu(bar, "Khám phá ▾", (
            (tr(self.ui_language, "observatory.hero"), self.show_observatory),
            ("NASA Explore · Năm nguy cơ", self.show_nasa_explore),
            ("Thư viện y khoa", self.show_medical_library),
            ("Cơ thể 3D", self.show_atlas),
        ))
        self.nav_crew = self._nav_button(bar, "Phi hành đoàn", self.show_mission)
        self.nav_more = self._nav_menu(bar, "Thêm ▾", (
            ("Hỏi AI", self.show_assistant),
            ("NASA Explore", self.show_nasa_explore),
            (tr(self.ui_language, "observatory.hero"), self.show_observatory),
            ("Thư viện y khoa", self.show_medical_library),
            ("Phi hành đoàn", self.show_mission),
            ("Hành trình chăm sóc", self.show_care),
            (tr(self.ui_language, "demo.portal.title"), self.show_simulated_briefing),
        ))
        self.observatory_menu_actions = (
            self.nav_science.menu().actions()[0],
            self.nav_more.menu().actions()[2],
        )
        # Browse is the sole route navigator: keep legacy buttons only as
        # dormant compatibility actions, never as duplicate visible chrome.
        for nav in (self.nav_home, self.nav_health, self.nav_monitor,
                    self.nav_ai, self.nav_science, self.nav_crew, self.nav_more):
            nav.hide()
        bar.addStretch(1)

        self._server_state = "checking"
        self.status = QLabel("○  Đang kiểm tra")
        self.status.setObjectName("connectionPill")
        self.status.setToolTip("Trạng thái HTTP Server tại địa chỉ cấu hình")
        bar.addWidget(self.status)
        # The sole visible connection indicator is inside Mission Operations.
        # This hidden label remains the localized source of truth for /health.
        self.status.hide()
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
        self.logout_button = QPushButton("Sign out" if self.ui_language == "en" else "Đăng xuất")
        self.logout_button.setObjectName("navButton")
        self.logout_button.clicked.connect(self.sign_out)
        self.logout_button.hide()
        bar.addWidget(self.logout_button)
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
        # Keep prior Portal available for compatibility without making it Home.
        self.shortcut_legacy_portal = QShortcut(QKeySequence("Alt+Shift+Home"), self)
        self.shortcut_legacy_portal.activated.connect(self.show_legacy_portal)
        self._retranslate_shell()
        self.pages.setCurrentWidget(self.login_page)
        self.check_server()
        self.heartbeat = QTimer(self)
        self.heartbeat.setInterval(30000)
        self.heartbeat.timeout.connect(self.check_server)
        self.heartbeat.start()
        # Native cold-start: first reuse an existing AETHERION loopback server;
        # only if refused, launch the installed local one. In parallel preseed
        # Q-0484's separate fictional-crew SQLite on a background thread.
        # This NEVER creates credentials or synthetic HTTP patient records.
        self.first_run_runtime = StartupRuntime(self.api_url, self)
        self.first_run_runtime.server_ready.connect(self.check_server)
        application = QApplication.instance()
        if application is not None:
            application.aboutToQuit.connect(self.first_run_runtime.stop)
        QTimer.singleShot(0, self.first_run_runtime.begin)

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
        for mode,icon in (("light","☀  "),("fusion","◐  "),("dark","☾  ")):
            act=QAction(icon+settings_tr(mode,self.ui_language),self.theme_menu)
            act.setCheckable(True)
            act.setChecked(self.preferences.mode==mode)
            act.triggered.connect(lambda checked=False,key=mode:self._change_mode(key))
            self.theme_menu.addAction(act)
        self.theme_menu.addSeparator()
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
        self.login_page.set_locale(self.ui_language)
        self.logout_button.setText("Sign out" if self.ui_language == "en" else "Đăng xuất")
        self.operations_home_page.set_locale(self.ui_language)
        self.simulated_briefing_page.set_locale(self.ui_language)
        self.synthetic_patient_page.set_locale(self.ui_language)
        self.portal_page.set_locale(self.ui_language)
        self.knowledge_browser_page.set_locale(self.ui_language)
        self.hackathon_demo_page.set_locale(self.ui_language)
        self.nav_more.menu().actions()[-1].setText(tr(self.ui_language, "demo.portal.title"))
        for page in (self.mission_control_page, self.personal_today_page,
                     self.medical_library_page, self.nasa_explore_page):
            page.set_locale(self.ui_language)
        for action in self.observatory_menu_actions:
            action.setText(tr(self.ui_language, "observatory.hero"))
        for section in (
            self.top_bar, self.footer_bar,
        ):
            translate_shell_widgets(section, self.ui_language)
        self.atlas_page.set_locale(self.ui_language)
        self.monitor_page.set_locale(self.ui_language)
        self.ecg_page.set_locale(self.ui_language)
        self.assistant_page.set_locale(self.ui_language)
        self.care_page.set_locale(self.ui_language)
        self.symptom_page.set_locale(self.ui_language)
        self.care_journal_page.set_locale(self.ui_language)
        # Resolve every main navigation item by its semantic route key:
        # shared strings like "Hành trình chăm sóc" have distinct contexts.
        for widget, key in (
            (self.nav_home, "main.nav.home"),
            (self.nav_health, "main.nav.health"),
            (self.nav_monitor, "main.nav.monitor"),
            (self.nav_ai, "main.nav.assistant"),
            (self.nav_science, "main.nav.explore"),
            (self.nav_crew, "main.nav.crew"),
        ):
            widget.setText(tr(self.ui_language, key))
        for menu_button, keys in (
            (self.nav_health, ("main.nav.health.today", "main.nav.care")),
            (self.nav_monitor, ("main.nav.monitor.overview", "main.nav.ecg", "main.nav.authorized")),
            (self.nav_science, ("observatory.hero", "main.nav.nasa",
                                "main.nav.library", "main.nav.atlas")),
            (self.nav_more, ("main.nav.assistant", "main.nav.nasa", "observatory.hero",
                             "main.nav.library", "main.nav.crew", "main.nav.care",
                             "demo.portal.title")),
        ):
            actions = menu_button.menu().actions()
            if len(actions) == len(keys):
                for action, key in zip(actions, keys):
                    action.setText(tr(self.ui_language, key))
        self.theme_button.setText(tr(self.ui_language, "main.theme.button"))
        self._render_server_status()
        self.language_button.setText(f"VI / EN · {self.ui_language.upper()}")
        self.language_button.setToolTip(tr(self.ui_language, "main.locale.tooltip"))
        self.language_button.setAccessibleName(tr(self.ui_language, "main.locale.tooltip"))
        self._build_theme_menu()
        self.settings_button.setText("⚙  "+settings_tr("settings",self.ui_language))
        self.nav_more.setText(settings_tr("more",self.ui_language)+" ▾")

    def _change_language(self):
        self.ui_language = "en" if self.ui_language == "vi" else "vi"
        self.preferences.set_language(self.ui_language)
        self._retranslate_shell()
        self.settings_page.retranslate()

    def _change_mode(self,mode: str):
        self.preferences.set_mode(mode)
        self._apply_preferences()

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
        self.operations_home_page.set_visuals(
            self.preferences.theme_name, self.preferences.reduce_motion,
            self.preferences.mode, self.preferences.animation_intensity,
        )
        self.simulated_briefing_page.set_visuals(
            self.preferences.theme_name, self.preferences.mode,
            self.preferences.reduce_motion, self.preferences.animation_intensity,
        )
        self.synthetic_patient_page.set_visuals(
            self.preferences.theme_name, self.preferences.mode,
        )
        self.settings_page.retranslate()
        self.knowledge_browser_page.set_visuals(
            self.preferences.theme_name, self.preferences.mode,
            self.preferences.reduce_motion, self.preferences.animation_intensity,
        )
        self.hackathon_demo_page.set_visuals(
            self.preferences.theme_name, self.preferences.mode,
            self.preferences.reduce_motion, self.preferences.animation_intensity,
        )
        self.ambient_controller.update_preferences(self.preferences)
        self.monitor_page.apply_theme(self.preferences)
        if self.ui_language != self.preferences.language:
            self.ui_language = self.preferences.language
            self._retranslate_shell()

    def open_theme_menu(self):
        self.show_settings()

    def _show_workspace_feature(self, route: str):
        """Keep Browse, Inspect and the bottom UTC conductor visible on routes."""
        if route in {"health", "mission", "crew", "monitor", "ecg", "assistant", "interview", "care"} and not self.access_token:
            self.pages.setCurrentWidget(self.login_page)
            return
        if not self.operations_home_page.show_hosted(route):
            raise ValueError(f"Unregistered native workspace: {route}")
        self.pages.setCurrentWidget(self.operations_home_page)

    def show_settings(self):
        self._show_workspace_feature("settings")

    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self, "nav_more"):
            # No legacy route button may reappear on resize: Browse is primary.
            for nav in (self.nav_home, self.nav_health, self.nav_monitor,
                        self.nav_ai, self.nav_science, self.nav_crew, self.nav_more):
                nav.hide()


    def _login_complete(self, payload: dict, base_url: str):
        """Unlock existing feature widgets with the actual bearer session."""
        self.api_url = base_url
        self.access_token = payload["access_token"]
        self.session_identity = payload["user"]
        for page in self.findChildren(QWidget):
            if hasattr(page, "api_url"):
                page.api_url = base_url
        self.logout_button.show()
        self.show_portal()
        self.check_server()
        request = QNetworkRequest(QUrl(base_url + "/api/v1/subjects"))
        request.setRawHeader(b"Authorization", ("Bearer " + self.access_token).encode("utf-8"))
        reply = self.network.get(request)
        expected_token = self.access_token
        def subjects_loaded():
            try:
                if self.access_token != expected_token:
                    return
                if reply.error() == QNetworkReply.NetworkError.NoError:
                    rows = json.loads(bytes(reply.readAll()).decode("utf-8")).get("subjects", [])
                    if rows:
                        self.open_personal_subject(rows[0]["subject_id"], expected_token)
                        self.show_portal()
            except (ValueError, KeyError, TypeError):
                pass
            finally:
                reply.deleteLater()
        reply.finished.connect(subjects_loaded)

    def sign_out(self):
        token = self.access_token
        self.access_token = ""
        self.session_identity = None
        self.logout_button.hide()
        self.pages.setCurrentWidget(self.login_page)
        self.personal_today_page.select_subject("", "")
        self.monitor_page.select_subject("", "")
        self.ecg_page.select_subject("", "")
        self.assistant_page.set_identity("", "")
        self.symptom_page.set_identity("", "")
        self.care_journal_page.set_identity("", "")
        if token:
            request = QNetworkRequest(QUrl(self.api_url + "/api/v1/auth/logout"))
            request.setRawHeader(b"Authorization", ("Bearer " + token).encode("utf-8"))
            reply = self.network.post(request, b"")
            reply.finished.connect(reply.deleteLater)

    def show_portal(self):
        """Home means the persistent native Mission Operations overview."""
        if not self.access_token:
            self.pages.setCurrentWidget(self.login_page)
            return
        self.pages.setCurrentWidget(self.operations_home_page)
        self.operations_home_page.show_overview()

    def show_legacy_portal(self):
        """Compatibility-only access; never the native app cold-start view."""
        if not self.access_token:
            self.pages.setCurrentWidget(self.login_page)
            return
        self.pages.setCurrentWidget(self.portal_page)

    def open_operations_route(self, route: str):
        """Resolve every source/health route through the original safe handlers."""
        if route not in ROUTE_IDS:
            return
        handler = {
            "mission": self.show_mission,
            "crew": self.show_mission,
            "health": self.show_personal,
            "monitor": self.show_monitor,
            "ecg": self.show_ecg,
            "assistant": self.show_assistant,
            "interview": self.show_symptom_interview,
            "care": self.show_care,
            "science": self.show_observatory,
            "hazards": self.show_nasa_explore,
            "medical_library": self.show_medical_library,
            "atlas": self.show_atlas,
            "settings": self.show_settings,
        }.get(route)
        if handler is not None:
            handler()

    def show_simulated_briefing(self):
        """Every Demo entry opens a provenance guide in the persistent shell."""
        self._show_workspace_feature("simulated_briefing")

    def start_simulated_demo(self):
        """Wait for startup's demo-only SQLite writer before opening Q-0484."""
        self.simulated_briefing_page.start.setEnabled(False)
        self.first_run_runtime.request_demo_ready(
            self._finish_simulated_demo_start
        )

    def _finish_simulated_demo_start(self, ready: bool):
        self.simulated_briefing_page.start.setEnabled(True)
        # A user may go Back while the asynchronous fixture writer finishes.
        # Do not unexpectedly replace their current screen with a late Demo.
        if self.operations_home_page.workspace_stack.currentWidget() is not self.simulated_briefing_page:
            return
        # Even on preseed failure, Q-0484's own widget exposes its normal
        # retry/error handling. Never substitute fake NASA or real crew data.
        self._show_workspace_feature("synthetic_patient")
        self.synthetic_patient_page.start()

    def show_personal(self):
        self._show_workspace_feature("health")

    def show_mission(self):
        self._show_workspace_feature("mission")

    def show_medical_library(self):
        self.medical_library_page.reload()
        self._show_workspace_feature("medical_library")

    def show_nasa_explore(self):
        self.nasa_explore_page.reload()
        self._show_workspace_feature("hazards")

    def show_observatory(self):
        """Open the real native article search on the canonical AETHERION Server."""
        self._show_workspace_feature("science")

    def show_hackathon_demo(self):
        """Genuine historical NASA MA-7, never the SIMULATED patient store."""
        self.hackathon_demo_page.show_briefing()
        self._show_workspace_feature("nasa_archive")

    def show_monitor(self):
        # Preserve the original Q-0477 authorization recheck and HTTP refresh.
        # Home's UTC time conductor is NOT bound to Monitoring without ACK.
        self.monitor_page.refresh()
        self._show_workspace_feature("monitor")

    def show_ecg(self):
        self.ecg_page.refresh()
        self._show_workspace_feature("ecg")

    def show_assistant(self):
        self.assistant_page.refresh_status()
        self._show_workspace_feature("assistant")

    def show_atlas(self):
        self._show_workspace_feature("atlas")

    def show_care(self):
        self._show_workspace_feature("care")
        self.care_journal_page.refresh()

    def show_symptom_interview(self):
        # Continue an existing D30 interview and preserve previously answered questions.
        previous = getattr(self.assistant_page, "symptom", None)
        if previous is not None:
            name = str(previous[0])
            answers = dict(getattr(self.assistant_page, "answers", {}))
            if self.symptom_page.active_symptoms != [name] or self.symptom_page.answers != answers:
                self.symptom_page.reset_interview()
                self.symptom_page.active_symptoms = [name]
                self.symptom_page.answers = answers
                self.symptom_page._selection_label()
                self.symptom_page._ask()
        self._show_workspace_feature("interview")

    def _open_care_from_interview(self, episode_id: str):
        self.care_journal_page.start_from_interview(episode_id)
        self._show_workspace_feature("care")

    def open_portal_route(self, route: str):
        if route not in PORTAL_ROUTES:
            return
        {
            "health": self.show_personal,
            "monitor": self.show_monitor,
            "assistant": self.show_assistant,
            "science": self.show_observatory,
            "crew": self.show_mission,
        }[route]()

    def open_personal_subject(self, subject_id: str, access_token: str):
        """Preserve the existing authorized Mission → Personal handoff."""
        self.personal_today_page.select_subject(subject_id, access_token)
        self.monitor_page.select_subject(subject_id, access_token)
        self.ecg_page.select_subject(subject_id, access_token)
        self.assistant_page.set_identity(subject_id, access_token)
        self.symptom_page.set_identity(subject_id, access_token)
        self.care_journal_page.set_identity(subject_id, access_token)
        self.show_personal()

    def show_help(self):
        QMessageBox.information(
            self, tr(self.ui_language, "main.help.title"),
            tr(self.ui_language, "main.help.body"),
        )

    def _render_server_status(self):
        """Language switching never starts a redundant network request."""
        state = self._server_state
        if state == "online":
            self.status.setText(tr(self.ui_language, "main.status.online"))
            self.status.setToolTip(tr(
                self.ui_language, "main.status.online.tooltip", url=self.api_url
            ))
        elif state == "offline":
            self.status.setText(tr(self.ui_language, "main.status.offline"))
            self.status.setToolTip(tr(
                self.ui_language, "main.status.offline.tooltip", url=self.api_url
            ))
        else:
            self.status.setText(tr(self.ui_language, "main.status.checking"))
            self.status.setToolTip(tr(self.ui_language, "main.status.tooltip"))
        # The operations status reflects this exact HTTP /health state; not demo data.
        self.operations_home_page.set_connection_state(self.status.text())

    def check_server(self):
        self._server_state = "checking"
        self._render_server_status()
        request = QNetworkRequest(QUrl(self.api_url + "/health"))
        reply = self.network.get(request)
        reply.finished.connect(lambda: self.finish_check(reply))

    def finish_check(self, reply):
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        error = reply.error()
        body = bytes(reply.readAll()).decode("utf-8", errors="replace")
        if error != QNetworkReply.NetworkError.NoError or code != 200 or '"status":"ok"' not in body.replace(" ", ""):
            self._server_state = "offline"
        else:
            self._server_state = "online"
        self._render_server_status()
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

