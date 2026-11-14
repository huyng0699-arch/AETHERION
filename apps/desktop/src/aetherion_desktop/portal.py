"""AETHERION native five-destination Portal (D00, owner design SPEC V3).

The page is usable while the API is offline. Decorations are not telemetry.
This module preserves the pure-data PORTAL_CARDS / PORTAL_ROUTES contract.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PortalCard:
    route: str
    title: str
    summary: str


PORTAL_CARDS: tuple[PortalCard, ...] = (
    PortalCard("health", "Sức khỏe của tôi", "Chỉ số, hành trình và nguồn dữ liệu của bạn"),
    PortalCard("monitor", "Theo dõi & ECG", "Đo lường, xu hướng và hồ sơ điện tim"),
    PortalCard("assistant", "Hỏi AI về sức khỏe", "Đặt câu hỏi và khám phá thông tin có nguồn"),
    PortalCard("science", "Khám phá khoa học", "Thư viện NASA, cơ thể và khoa học sức khỏe"),
    PortalCard("crew", "Phi hành đoàn", "Theo dõi nhiệm vụ và hỗ trợ đồng đội"),
)
PORTAL_ROUTES = frozenset(card.route for card in PORTAL_CARDS)


def build_portal_page(parent=None, *, theme_name: str = "orbit", reduce_motion: bool = False):
    """Create a beautiful *native* Qt Portal. No server call or data fabrication."""
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
        QVBoxLayout, QWidget,
    )
    from .visual_theme import AmbientBackdrop

    class PortalCardPanel(QFrame):
        clicked = Signal(str)

        def __init__(self, route: str):
            super().__init__()
            self.route = route
            self.setCursor(Qt.CursorShape.PointingHandCursor)

        def mouseReleaseEvent(self, event):
            if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(event.position().toPoint()):
                self.clicked.emit(self.route)
            super().mouseReleaseEvent(event)

    class PortalPage(QWidget):
        route_requested = Signal(str)
        theme_requested = Signal()

        def __init__(self):
            super().__init__(parent)
            self.setObjectName("aetherionPortal")
            self.ambient = AmbientBackdrop(self, theme_name, reduce_motion)
            self.ambient.lower()
            root = QVBoxLayout(self)
            root.setContentsMargins(35, 23, 35, 25)
            root.setSpacing(11)

            upper = QHBoxLayout()
            small = QLabel("TRUY TINH  /  MISSION HEALTH INTELLIGENCE")
            small.setObjectName("eyebrow")
            upper.addWidget(small)
            upper.addStretch(1)
            edition = QLabel("AETHERION  •  EARTH → BEYOND")
            edition.setObjectName("pageHint")
            edition.setAlignment(Qt.AlignmentFlag.AlignRight)
            upper.addWidget(edition)
            root.addLayout(upper)

            hero = QHBoxLayout()
            hero.setSpacing(20)
            hero_copy = QVBoxLayout()
            hero_copy.setSpacing(6)
            hero_copy.addStretch(1)
            title = QLabel("Sức khỏe, có chiều sâu.")
            title.setObjectName("heroTitle")
            title.setWordWrap(True)
            hero_copy.addWidget(title)
            subtitle = QLabel("Chọn nơi bạn muốn bắt đầu. Mọi số đo đều phải có nguồn và thời gian rõ ràng.")
            subtitle.setObjectName("heroCopy")
            subtitle.setWordWrap(True)
            hero_copy.addWidget(subtitle)
            hero_copy.addStretch(1)
            hero.addLayout(hero_copy, 1)
            side = QLabel("01 / HOME\n\nONE HEALTH\nBEYOND EARTH")
            side.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            side.setStyleSheet("font-size:13px; font-weight:600; color:rgba(186,218,234,170); letter-spacing:2px;")
            hero.addWidget(side)
            root.addLayout(hero, 2)

            grid = QGridLayout()
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(15)
            grid.setVerticalSpacing(14)
            marks = ("◎", "⌁", "✧", "✦", "◇")
            self.card_buttons: dict[str, QPushButton] = {}
            for index, card in enumerate(PORTAL_CARDS):
                panel = PortalCardPanel(card.route)
                panel.clicked.connect(self.route_requested.emit)
                panel.setObjectName("portalCard")
                content = QVBoxLayout(panel)
                content.setContentsMargins(21, 15, 21, 14)
                content.setSpacing(5)
                head = QHBoxLayout()
                mark = QLabel(f"{marks[index]}   {index + 1:02d} / 05")
                mark.setObjectName("cardNumber")
                head.addWidget(mark)
                head.addStretch()
                arrow = QLabel("↗")
                arrow.setObjectName("cardNumber")
                head.addWidget(arrow)
                content.addLayout(head)
                action = QPushButton(card.title)
                action.setObjectName("portalCardButton")
                action.setAccessibleName(card.title)
                action.setToolTip(f"Mở {card.title}")
                action.setCursor(Qt.CursorShape.PointingHandCursor)
                action.setMinimumHeight(36)
                action.clicked.connect(lambda checked=False, key=card.route: self.route_requested.emit(key))
                content.addWidget(action)
                description = QLabel(card.summary)
                description.setObjectName("cardDescription")
                description.setWordWrap(True)
                content.addWidget(description)
                self.card_buttons[card.route] = action
                if index == 4:
                    grid.addWidget(panel, 2, 0, 1, 2)
                else:
                    row, column = divmod(index, 2)
                    grid.addWidget(panel, row, column)
            root.addLayout(grid, 8)

            footer = QHBoxLayout()
            footer.setSpacing(12)
            trust = QLabel("●  LOCAL-FIRST   /   DỮ LIỆU CÓ NGUỒN   /   KHÔNG TẠO SỐ ĐO GIẢ")
            trust.setObjectName("pageHint")
            footer.addWidget(trust)
            footer.addStretch()
            theme = QPushButton("◐  Đổi giao diện")
            theme.setAccessibleName("Đổi giao diện AETHERION")
            theme.setObjectName("navButton")
            theme.clicked.connect(self.theme_requested.emit)
            footer.addWidget(theme)
            root.addLayout(footer)

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self.ambient.setGeometry(self.rect())
            self.ambient.lower()

        def set_visuals(self, name: str, motion_reduced: bool):
            self.ambient.set_visuals(name, motion_reduced)

    return PortalPage()
