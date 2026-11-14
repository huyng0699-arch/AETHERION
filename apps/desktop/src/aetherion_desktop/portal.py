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


def build_portal_page(parent=None, *, theme_name: str = "daybreak", reduce_motion: bool = False, locale: str = "vi",
                      mode: str = "light", intensity: int = 48):
    """Create a beautiful *native* Qt Portal. No server call or data fabrication."""
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtWidgets import (
        QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
        QVBoxLayout, QWidget,
    )
    from .visual_theme import AmbientBackdrop
    from .localization import normalize_locale, tr

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
        demo_requested = Signal()

        def __init__(self):
            super().__init__(parent)
            self.language = normalize_locale(locale)
            self.setObjectName("aetherionPortal")
            self.ambient = AmbientBackdrop(self, theme_name, reduce_motion, mode, intensity)
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
            title = QLabel(tr(self.language, "portal.hero.title"))
            self.hero_title = title
            title.setObjectName("heroTitle")
            title.setWordWrap(True)
            hero_copy.addWidget(title)
            subtitle = QLabel(tr(self.language, "portal.hero.subtitle"))
            self.hero_subtitle = subtitle
            subtitle.setObjectName("heroCopy")
            subtitle.setWordWrap(True)
            hero_copy.addWidget(subtitle)
            hero_copy.addStretch(1)
            hero.addLayout(hero_copy, 1)
            side = QLabel("01 / HOME\n\nONE HEALTH\nBEYOND EARTH")
            side.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            side.setObjectName("pageHint")
            hero.addWidget(side)
            root.addLayout(hero, 2)

            grid = QGridLayout()
            grid.setContentsMargins(0, 0, 0, 0)
            grid.setHorizontalSpacing(15)
            grid.setVerticalSpacing(14)
            marks = ("◎", "⌁", "✧", "✦", "◇")
            self.card_buttons: dict[str, QPushButton] = {}
            self.card_descriptions: dict[str, QLabel] = {}
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
                card_title = tr(self.language, f"portal.card.{card.route}.title")
                action = QPushButton(card_title)
                action.setObjectName("portalCardButton")
                action.setAccessibleName(card_title)
                action.setToolTip(tr(self.language, "portal.open", title=card_title))
                action.setCursor(Qt.CursorShape.PointingHandCursor)
                action.setMinimumHeight(36)
                action.clicked.connect(lambda checked=False, key=card.route: self.route_requested.emit(key))
                content.addWidget(action)
                description = QLabel(tr(self.language, f"portal.card.{card.route}.summary"))
                description.setObjectName("cardDescription")
                description.setWordWrap(True)
                content.addWidget(description)
                self.card_buttons[card.route] = action
                self.card_descriptions[card.route] = description
                if index == 4:
                    grid.addWidget(panel, 2, 0, 1, 2)
                else:
                    row, column = divmod(index, 2)
                    grid.addWidget(panel, row, column)
            root.addLayout(grid, 8)

            # The owner's hackathon entry is an extra banner, NOT a sixth
            # medical card: preserve the designed five destination Portal.
            demo_strip = QFrame()
            demo_strip.setObjectName("contentPanel")
            strip = QHBoxLayout(demo_strip)
            strip.setContentsMargins(17, 9, 17, 9)
            strip.setSpacing(13)
            self.demo_caption = QLabel(tr(self.language, "demo.portal.summary"))
            self.demo_caption.setObjectName("pageHint")
            self.demo_caption.setWordWrap(True)
            strip.addWidget(self.demo_caption, 1)
            self.demo_button = QPushButton(tr(self.language, "demo.portal.title"))
            self.demo_button.setObjectName("primaryAction")
            self.demo_button.setAccessibleName(tr(self.language, "demo.portal.open"))
            self.demo_button.clicked.connect(self.demo_requested.emit)
            strip.addWidget(self.demo_button)
            root.addWidget(demo_strip)

            footer = QHBoxLayout()
            footer.setSpacing(12)
            trust = QLabel(tr(self.language, "portal.footer.trust"))
            self.trust_label = trust
            trust.setObjectName("pageHint")
            footer.addWidget(trust)
            footer.addStretch()
            theme = QPushButton(tr(self.language, "portal.theme"))
            self.theme_button = theme
            theme.setAccessibleName(tr(self.language, "portal.theme.accessible"))
            theme.setObjectName("navButton")
            theme.clicked.connect(self.theme_requested.emit)
            footer.addWidget(theme)
            root.addLayout(footer)

        def set_locale(self, locale: str):
            """Update every Portal UI string without changing routes or clinical data."""
            self.language = normalize_locale(locale)
            self.hero_title.setText(tr(self.language, "portal.hero.title"))
            self.hero_subtitle.setText(tr(self.language, "portal.hero.subtitle"))
            self.trust_label.setText(tr(self.language, "portal.footer.trust"))
            self.demo_caption.setText(tr(self.language, "demo.portal.summary"))
            self.demo_button.setText(tr(self.language, "demo.portal.title"))
            self.demo_button.setAccessibleName(tr(self.language, "demo.portal.open"))
            self.theme_button.setText(tr(self.language, "portal.theme"))
            self.theme_button.setAccessibleName(tr(self.language, "portal.theme.accessible"))
            for route, button in self.card_buttons.items():
                title = tr(self.language, f"portal.card.{route}.title")
                button.setText(title)
                button.setAccessibleName(title)
                button.setToolTip(tr(self.language, "portal.open", title=title))
                self.card_descriptions[route].setText(tr(self.language, f"portal.card.{route}.summary"))

        def resizeEvent(self, event):
            super().resizeEvent(event)
            self.ambient.setGeometry(self.rect())
            self.ambient.lower()

        def set_visuals(self, name: str, motion_reduced: bool, mode: str = "light", intensity: int = 48):
            self.ambient.set_visuals(name, motion_reduced, mode, intensity)

    return PortalPage()
