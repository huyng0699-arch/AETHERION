"""Native Qt visual system for AETHERION.

Deep ambient background is drawn procedurally under the UI. It is decorative,
never medical imagery or an asserted live spacecraft feed. Theme choices are
stored only in local QSettings; no user health data enters the theme system.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import (
    QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient,
)
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class Theme:
    title: str
    base: str
    top: str
    surface: str
    border: str
    accent: str
    second: str
    text: str
    muted: str


THEMES: dict[str, Theme] = {
    "orbit": Theme("Quỹ đạo Trái Đất", "#071421", "#0E2840", "#10253A", "#31526B", "#89E3DC", "#7EAEFF", "#F0F8FF", "#A5BED1"),
    "galaxy": Theme("Dải ngân hà", "#0C1028", "#241A49", "#1C1E3A", "#4B466B", "#B8A0FF", "#8ECAE9", "#F5F3FF", "#B9B5D4"),
    "rain": Theme("Mưa đêm", "#0A1720", "#1C3440", "#132B33", "#3D5962", "#8DD9E0", "#91B9DE", "#F0FAFC", "#ADC4C9"),
    "ocean": Theme("Dòng nước", "#06252D", "#0A3C4A", "#103943", "#35636E", "#74D9CE", "#88C8F1", "#E9FCFA", "#B0D4D7"),
    "minimal": Theme("Tối giản", "#101923", "#162635", "#1B2B38", "#415464", "#A7D8E6", "#B8D5E8", "#EDF5F9", "#B9C9D3"),
}


class AmbientBackdrop(QWidget):
    """Small, deterministic, low-rate animated painter BELOW all user controls."""

    def __init__(self, parent=None, theme_name: str = "orbit", reduce_motion: bool = False):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.theme_name = theme_name if theme_name in THEMES else "orbit"
        self.reduce_motion = reduce_motion
        self.phase = 0.0
        rng = random.Random(2050)
        self.stars = [(rng.random(), rng.random(), rng.uniform(0.4, 1.8), rng.uniform(0.3, 1.0)) for _ in range(115)]
        self.drops = [(rng.random(), rng.random(), rng.uniform(0.006, 0.022), rng.uniform(5, 15)) for _ in range(88)]
        self.timer = QTimer(self)
        self.timer.setInterval(70)  # <=15 updates/sec for a purely decorative surface
        self.timer.timeout.connect(self._next_frame)
        self._update_timer()

    def set_visuals(self, name: str, reduce_motion: bool):
        self.theme_name = name if name in THEMES else "orbit"
        self.reduce_motion = reduce_motion
        self._update_timer()
        self.update()

    def _update_timer(self):
        if not self.reduce_motion and self.theme_name != "minimal" and self.isVisible():
            self.timer.start()
        else:
            self.timer.stop()

    def showEvent(self, event):
        super().showEvent(event)
        self._update_timer()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def _next_frame(self):
        self.phase = (self.phase + 0.007) % 1.0
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w < 1 or h < 1:
            return
        t = THEMES[self.theme_name]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QLinearGradient(0, 0, w, h)
        bg.setColorAt(0, QColor(t.base))
        bg.setColorAt(0.62, QColor(t.top))
        bg.setColorAt(1, QColor(t.base))
        painter.fillRect(self.rect(), bg)

        if self.theme_name == "minimal":
            painter.end()
            return
        self._glow(painter, w * 0.77, h * 0.22, w * 0.46, t.accent, 24)
        self._glow(painter, w * 0.21, h * 0.81, w * 0.55, t.second, 13)
        if self.theme_name in ("orbit", "galaxy"):
            self._space(painter, w, h, t)
        elif self.theme_name == "rain":
            self._rain(painter, w, h, t)
        else:
            self._ocean(painter, w, h, t)
        # Final dark tint keeps typography above this layer readable.
        painter.fillRect(self.rect(), QColor(4, 12, 22, 46))
        painter.end()

    @staticmethod
    def _glow(painter, x, y, radius, color, opacity):
        grad = QRadialGradient(x, y, radius)
        c = QColor(color)
        c.setAlpha(opacity)
        grad.setColorAt(0, c)
        c.setAlpha(0)
        grad.setColorAt(1, c)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawEllipse(int(x - radius), int(y - radius), int(2 * radius), int(2 * radius))

    def _space(self, painter, w, h, theme):
        for x, y, size, lum in self.stars:
            twinkle = 0.82 if self.reduce_motion else 0.70 + 0.26 * math.sin((x + y + self.phase) * 6.283)
            painter.setBrush(QColor(224, 241, 255, int(135 * lum * twinkle)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(int(x * w), int(y * h), max(1, int(size)), max(1, int(size)))
        cx, cy = w * 0.86, h * 0.55
        radius = min(w * 0.19, h * 0.30)
        # Atmospheric disk is purely decorative; not a satellite feed.
        globe = QRadialGradient(cx - radius * 0.31, cy - radius * 0.41, radius * 1.5)
        globe.setColorAt(0.0, QColor("#497EA3" if self.theme_name == "orbit" else "#776CBA"))
        globe.setColorAt(0.43, QColor("#143B67" if self.theme_name == "orbit" else "#393060"))
        globe.setColorAt(0.96, QColor(6, 17, 33, 230))
        globe.setColorAt(1, QColor(3, 8, 20, 255))
        painter.setPen(QPen(QColor(theme.accent + "44"), 1.5))
        painter.setBrush(globe)
        painter.drawEllipse(int(cx - radius), int(cy - radius), int(2 * radius), int(2 * radius))
        painter.save()
        painter.translate(cx, cy)
        painter.rotate(-18)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(141, 204, 224, 40), 1))
        painter.drawEllipse(int(-radius * 1.56), int(-radius * 0.51), int(radius * 3.12), int(radius * 1.02))
        painter.setPen(QPen(QColor(152, 225, 235, 85), 2))
        painter.drawArc(int(-radius * 1.56), int(-radius * 0.51), int(radius * 3.12), int(radius * 1.02), int(self.phase * 5760), 1250)
        painter.restore()

    def _rain(self, painter, w, h, theme):
        painter.setPen(QPen(QColor(149, 207, 224, 61), 1))
        for x, y, velocity, length in self.drops:
            dy = ((y + (0 if self.reduce_motion else self.phase * velocity * 50)) % 1.0) * h
            px = int(x * w)
            painter.drawLine(px, int(dy), px - 4, int(dy + length))

    def _ocean(self, painter, w, h, theme):
        for n in range(13):
            ypos = h * (0.32 + n * 0.058)
            painter.setPen(QPen(QColor(111, 224, 223, max(8, 43 - n * 2)), 1.2))
            old = None
            for i in range(0, w + 12, 12):
                y = ypos + math.sin((i / max(w, 1)) * 12 + n * 0.44 + self.phase * 6.28) * (5 + n * 0.5)
                if old is not None:
                    painter.drawLine(old[0], int(old[1]), i, int(y))
                old = (i, y)


class VisualPreferences:
    """Theme/typography settings, intentionally distinct from health data."""

    def __init__(self):
        self.settings = QSettings("TRUY TINH", "AETHERION")
        stored = str(self.settings.value("visual/theme", "orbit"))
        self.theme_name = stored if stored in THEMES else "orbit"
        self.reduce_motion = str(self.settings.value("visual/reduce_motion", "false")).lower() == "true"
        self.font_size = int(self.settings.value("visual/font_size", 10))
        self.font_size = max(9, min(13, self.font_size))

    def set_theme(self, theme_name: str):
        if theme_name not in THEMES:
            return
        self.theme_name = theme_name
        self.settings.setValue("visual/theme", theme_name)

    def set_reduced_motion(self, enabled: bool):
        self.reduce_motion = bool(enabled)
        self.settings.setValue("visual/reduce_motion", self.reduce_motion)

    def set_font_size(self, size: int):
        self.font_size = max(9, min(13, int(size)))
        self.settings.setValue("visual/font_size", self.font_size)

    def apply(self, app):
        theme = THEMES[self.theme_name]
        font = QFont("Segoe UI", self.font_size)
        app.setFont(font)
        app.setStyleSheet(make_stylesheet(theme))


def make_stylesheet(t: Theme) -> str:
    return """
    QMainWindow, QWidget { color: %(text)s; font-family: 'Segoe UI'; }
    QMainWindow { background: %(base)s; }
    QWidget#appRoot { background: %(base)s; }
    QFrame#topBar { background: %(base)s; border-bottom:1px solid %(border)s; }
    QLabel { background:transparent; }
    QLabel#wordmark { color:%(text)s; font-size:17px; font-weight:800; letter-spacing:2px; }
    QLabel#eyebrow { color:%(accent)s; font-size:11px; font-weight:700; letter-spacing:2px; }
    QLabel#heroTitle { color:%(text)s; font-size:34px; font-weight:800; }
    QLabel#heroCopy { color:%(muted)s; font-size:15px; }
    QLabel#cardNumber { color:%(accent)s; font-size:12px; letter-spacing:1px; }
    QLabel#cardDescription { color:%(muted)s; font-size:13px; }
    QLabel#connectionPill { background:%(surface)s; color:%(muted)s; border:1px solid %(border)s; border-radius:13px; padding:7px 11px; }
    QLabel#pageHint, QLabel#detail { color:%(muted)s; font-size:13px; }
    QLabel#heading { color:%(text)s; font-size:25px; font-weight:700; }
    QFrame#portalCard { background:rgba(22,41,59,215); border:1px solid %(border)s; border-radius:17px; }
    QFrame#portalCard:hover { background:rgba(32,58,78,235); border:1px solid %(accent)s; }
    QFrame#surface, QFrame#contentPanel { background:%(surface)s; border:1px solid %(border)s; border-radius:15px; }
    QPushButton { background:%(surface)s; color:%(text)s; border:1px solid %(border)s; border-radius:11px; padding:9px 14px; min-height:22px; }
    QPushButton:hover { border-color:%(accent)s; background:%(top)s; }
    QPushButton:focus { border:2px solid %(accent)s; }
    QPushButton#brandButton { background:transparent; border:0; font-size:17px; font-weight:800; letter-spacing:2px; color:%(text)s; padding:8px 0; }
    QPushButton#navButton { background:transparent; border:0; font-size:12px; font-weight:600; padding:9px 10px; }
    QPushButton#navButton:hover { background:%(surface)s; border-radius:9px; }
    QPushButton#portalCardButton { background:transparent; border:0; padding:0; text-align:left; font-weight:700; font-size:19px; min-height:33px; }
    QPushButton#portalCardButton:hover { color:%(accent)s; }
    QPushButton#primaryAction { background:%(accent)s; color:%(base)s; border:0; font-weight:750; }
    QPushButton#primaryAction:hover { background:%(second)s; }
    QToolButton { background:transparent; border:1px solid %(border)s; border-radius:10px; color:%(text)s; padding:9px; }
    QToolButton:hover { border-color:%(accent)s; }
    QTableWidget, QTableView, QListView, QTreeView { background:%(surface)s; alternate-background-color:%(top)s; color:%(text)s; border:1px solid %(border)s; gridline-color:%(border)s; selection-background-color:%(top)s; }
    QHeaderView::section { background:%(top)s; color:%(text)s; border:0; border-bottom:1px solid %(border)s; padding:8px; }
    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit { background:%(surface)s; border:1px solid %(border)s; border-radius:8px; padding:7px; color:%(text)s; }
    QMenu { background:%(surface)s; border:1px solid %(border)s; padding:6px; color:%(text)s; }
    QMenu::item { padding:9px 24px; border-radius:6px; }
    QMenu::item:selected { background:%(top)s; }
    QScrollArea, QScrollArea QWidget#qt_scrollarea_viewport { background:transparent; border:0; }
    """ % {"base":t.base,"top":t.top,"surface":t.surface,"border":t.border,"accent":t.accent,"second":t.second,"text":t.text,"muted":t.muted}
