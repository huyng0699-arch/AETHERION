"""Native Windows/Qt starter. Deliberately does not invent health data."""

import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget, QMessageBox,
)

from .portal import PORTAL_ROUTES, build_portal_page
from .medical_library import build_medical_library_page
from .mission_control import build_mission_control_page
from .features.personal.authorized_today import AuthorizedPersonalTodayPage

SECTIONS = [
    ("Mission Control", "Mission Control", "Crew overview and health monitoring will appear here once trustworthy observations are available."),
    ("Personal Health", "Personal Health", "No measurements are loaded. A healthy user does not have to enter symptoms to open the application."),
    ("Body Atlas", "Body Atlas", "Interactive 3D anatomy is planned; no non-functional static image is presented as 3D."),
    ("Explore", "Explore Space Health", "Explore NASA's five human-spaceflight hazards through sourced content in a future release."),
    ("Care", "Care Journey", "GATHER → EVALUATE → ACT → RECHECK: the supported care workflow is not yet implemented."),
    ("Guide", "Medical Guide", "A provenance-reviewed medical knowledge base and optional AI guidance are planned."),
]


class AetherionWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AETHERION | Mission Health")
        self.resize(1180, 740)
        self.api_url = os.environ.get("AETHERION_API_URL", "http://127.0.0.1:8765").rstrip("/")
        self.network = QNetworkAccessManager(self)
        self.setStyleSheet(
            "QMainWindow, QWidget { background:#081422; color:#ecf4ff; font-family:'Segoe UI'; }"
            "QLabel#heading { font-size:30px; font-weight:700; }"
            "QLabel#detail { color:#a9bdd5; font-size:15px; }"
            "QFrame#surface { background:#10243a; border:1px solid #29435e; border-radius:15px; }"
            "QPushButton { background:#17314d; color:#f3f8ff; border:1px solid #2c5070; "
            "border-radius:9px; padding:11px 14px; }"
            "QPushButton:hover { background:#215176; }"
        )

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(28, 22, 28, 22)
        outer.setSpacing(20)

        brand = QPushButton("AETHERION  /  TRUY TINH")
        brand.clicked.connect(self.show_portal)
        brand.setStyleSheet("font-size:14px; font-weight:700; color:#74dce4; letter-spacing:2px;")
        outer.addWidget(brand)

        nav = QHBoxLayout()
        nav.setSpacing(7)
        self.pages = QStackedWidget()
        self.portal_page = build_portal_page()
        self.portal_page.route_requested.connect(self.open_portal_route)
        self.pages.addWidget(self.portal_page)
        home_button = QPushButton("Trang đầu")
        home_button.clicked.connect(self.show_portal)
        nav.addWidget(home_button)
        for index, (button_name, heading, message) in enumerate(SECTIONS):
            button = QPushButton(button_name)
            button.clicked.connect(lambda checked=False, i=index: self.pages.setCurrentIndex(i + 1))
            nav.addWidget(button)
            if index == 0:
                # Mission Control loads live data only after explicit local authentication.
                self.mission_control_page = build_mission_control_page(self.api_url, self.network)
                self.pages.addWidget(self.mission_control_page)
                continue
            if index == 1:
                # Reuse the local authenticated session; never invent a profile.
                self.personal_today_page = AuthorizedPersonalTodayPage(self.api_url, self.network)
                self.pages.addWidget(self.personal_today_page)
                continue
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(20, 30, 20, 30)
            title = QLabel(heading)
            title.setObjectName("heading")
            layout.addWidget(title)
            card = QFrame()
            card.setObjectName("surface")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(25, 24, 25, 24)
            content = QLabel(message)
            content.setWordWrap(True)
            content.setObjectName("detail")
            card_layout.addWidget(content)
            layout.addWidget(card)
            layout.addStretch()
            self.pages.addWidget(page)
        # One explicit Mission -> Personal handoff; preserve identity on Back.
        self.mission_control_page.subject_activated.connect(self.open_personal_subject)
        # Native QWidget, not a browser or replacement landing page.
        self.medical_library_page = build_medical_library_page()
        self.pages.addWidget(self.medical_library_page)
        library_button = QPushButton("Medical Library")
        library_button.clicked.connect(self.show_medical_library)
        nav.addWidget(library_button)
        outer.addLayout(nav)
        outer.addWidget(self.pages, 1)

        status_row = QHBoxLayout()
        self.status = QLabel("Local API: not checked")
        status_row.addWidget(self.status, 1)
        check = QPushButton("Check local server")
        check.clicked.connect(self.check_server)
        status_row.addWidget(check)
        outer.addLayout(status_row)

        foot = QLabel("Independent Team TRUY TINH prototype • Not a medical device • No live sensors connected")
        foot.setStyleSheet("font-size:12px;color:#7892af;")
        outer.addWidget(foot)
        self.setCentralWidget(central)
        self.pages.setCurrentWidget(self.portal_page)
        self.check_server()

    def show_portal(self) -> None:
        """Portal is always reachable, including while the server is offline."""
        self.pages.setCurrentWidget(self.portal_page)

    def open_portal_route(self, route: str) -> None:
        """Route only to implemented native views; do not fake unavailable AI/ECG."""
        if route not in PORTAL_ROUTES:
            return
        if route == "health":
            self.pages.setCurrentWidget(self.personal_today_page)
        elif route in ("monitor", "crew"):
            self.pages.setCurrentWidget(self.mission_control_page)
            if route == "monitor":
                self.mission_control_page.status.setText(
                    "Recorded observations require authorization; ECG is not yet connected."
                )
        elif route == "science":
            self.show_medical_library()
        elif route == "assistant":
            QMessageBox.information(self, "AI chưa khả dụng",
                "Chưa có AI đã xác thực trong ứng dụng này. Không đưa ra chẩn đoán hoặc kết quả giả.")

    def open_personal_subject(self, subject_id: str, access_token: str) -> None:
        """Open the precise subject selected in Mission using the same session."""
        self.personal_today_page.select_subject(subject_id, access_token)
        self.pages.setCurrentWidget(self.personal_today_page)

    def show_medical_library(self) -> None:
        self.medical_library_page.reload()
        self.pages.setCurrentWidget(self.medical_library_page)

    def check_server(self) -> None:
        self.status.setText("Local API: checking…")
        request = QNetworkRequest(QUrl(self.api_url + "/health"))
        reply = self.network.get(request)
        reply.finished.connect(lambda: self.finish_check(reply))

    def finish_check(self, reply) -> None:
        error = reply.error()
        body = bytes(reply.readAll()).decode("utf-8", errors="replace")
        if error or '"status":"ok"' not in body.replace(" ", ""):
            self.status.setText("Local API: unavailable — start the server in another terminal")
        else:
            self.status.setText("Local API: connected — verified response from /health")
        reply.deleteLater()


def main() -> int:
    app = QApplication(sys.argv)
    window = AetherionWindow()
    window.show()
    return app.exec()
