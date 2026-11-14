"""Native, local-only visual engine for AETHERION Desktop.

Ambient art is purely decorative (never patient data or live NASA imagery).
LIGHT / DARK / FUSION are independent of theme palette; colors are derived
per mode to keep labels, tables and medical UI legible. Settings are local.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import QWidget


@dataclass(frozen=True)
class Theme:
    title: str
    scene: str
    accent: str
    second: str
    light: str
    dark: str


# A genuinely varied, bright-first collection. Unlike a set of duplicate
# wallpapers, each palette retains its own accent and procedural scene.
THEMES: dict[str, Theme] = {
    "daybreak": Theme("Bình minh", "sky", "#E47A4D", "#F8BE72", "#FFF8F0", "#283C58"),
    "spring": Theme("Vườn mùa xuân", "leaf", "#3F9E78", "#B4D989", "#F5FCF5", "#183F3F"),
    "orchid": Theme("Lan tím", "bloom", "#8B69D8", "#E5B3D8", "#FBF7FF", "#302A58"),
    "coral": Theme("San hô", "ocean", "#E56F74", "#67C7D8", "#FFF9F7", "#233D59"),
    "aurora": Theme("Cực quang", "nebula", "#3CB5B8", "#AC85EB", "#F3FAFF", "#183F55"),
    "lavender": Theme("Oải hương", "bloom", "#8578CB", "#B6C4EF", "#F8F6FF", "#292E52"),
    "ocean": Theme("Dòng nước", "ocean", "#269DB3", "#78D5C6", "#F2FBFF", "#153A50"),
    "forest": Theme("Rừng sớm", "leaf", "#3A947A", "#D4BA6A", "#F5FBF0", "#224535"),
    "orbit": Theme("Quỹ đạo Trái Đất", "orbit", "#398FCB", "#79D2CF", "#F3F9FF", "#182E52"),
    "galaxy": Theme("Ngân hà", "nebula", "#9376D9", "#DB9ED8", "#F8F7FF", "#292A53"),
    "rain": Theme("Mưa trong veo", "rain", "#429AC5", "#8DCEC9", "#F1FAFD", "#223C53"),
    "lotus": Theme("Hoa sen", "bloom", "#D176A2", "#8FB78B", "#FFF7F9", "#46364F"),
    "golden": Theme("Nắng mật ong", "sky", "#BE8B35", "#E3B76B", "#FFF9E8", "#4D3C3D"),
    "minimal": Theme("Tối giản thanh lịch", "minimal", "#6084AB", "#88A8D3", "#F8FAFE", "#26364B"),
}
MODES = ("light", "dark", "fusion")
LANGUAGES = ("vi", "en")
FONTS = ("Segoe UI", "Arial", "Noto Sans", "Inter", "Roboto")


def _mix(first: str | QColor, second: str | QColor, proportion: float) -> QColor:
    a, b = QColor(first), QColor(second)
    p = min(1.0, max(0.0, proportion))
    return QColor(round(a.red() * (1-p) + b.red() * p),
                  round(a.green() * (1-p) + b.green() * p),
                  round(a.blue() * (1-p) + b.blue() * p))


def _hex(color: str | QColor) -> str:
    return QColor(color).name(QColor.NameFormat.HexRgb)


@dataclass(frozen=True)
class Palette:
    base: str
    top: str
    surface: str
    surface_alt: str
    border: str
    accent: str
    second: str
    text: str
    muted: str
    header: str
    header_text: str
    card: str
    card_hover: str
    on_accent: str


def palette_for(theme_name: str, mode: str, high_contrast: bool = False, accent_override: str = "") -> Palette:
    theme = THEMES.get(theme_name, THEMES["daybreak"])
    mode = mode if mode in MODES else "light"
    accent = _hex(accent_override) if QColor(accent_override).isValid() else theme.accent
    if mode == "dark":
        base = _hex(_mix(theme.dark, "#334D68", 0.21))  # lucid, not black
        surface = _hex(_mix(theme.dark, "#50617D", 0.25))
        top = _hex(_mix(theme.dark, theme.second, 0.22))
        return Palette(base, top, surface, _hex(_mix(surface, "#FFFFFF", .07)),
                       "#61738B" if high_contrast else "#52667E",
                       _hex(_mix(accent, "#F4FFFF", .24)), theme.second,
                       "#FFFFFF", "#D6E4F0", "#223B56", "#FFFFFF",
                       _hex(_mix(surface, theme.second, .08)),
                       _hex(_mix(surface, "#FFFFFF", .13)), "#122638")
    if mode == "fusion":
        base = _hex(_mix(theme.light, "#D7E8F2", .31))
        top = _hex(_mix(theme.dark, theme.second, .40))
        return Palette(base, top, "#FFFFFF", "#F3F7FC",
                       "#738FAD" if high_contrast else "#D6E1EB", accent, theme.second,
                       "#193046", "#4F667A", "#263F5D", "#FFFFFF",
                       "#FFFFFF", _hex(_mix(theme.light, theme.second, .23)), "#13293B")
    # Light mode is deliberately the default and never a dim navy-only window.
    base = theme.light
    return Palette(base, _hex(_mix(theme.light, theme.second, .22)),
                   "#FFFFFF", _hex(_mix(theme.light, "#FFFFFF", .50)),
                   "#8AA4B7" if high_contrast else "#D5E2EB",
                   accent, theme.second, "#203348", "#536C7D",
                   "#FFFFFF", "#203348", "#FFFFFF",
                   _hex(_mix(theme.light, theme.second, .13)), "#13293B")


class AmbientBackdrop(QWidget):
    """Efficient 15 FPS native QPainter artwork, beneath interactive children."""

    def __init__(self, parent=None, theme_name: str = "daybreak", reduce_motion: bool = False,
                 mode: str = "light", intensity: int = 48):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.theme_name = theme_name if theme_name in THEMES else "daybreak"
        self.mode = mode if mode in MODES else "light"
        self.reduce_motion = bool(reduce_motion)
        self.intensity = max(0, min(100, intensity))
        self.phase = 0.0
        rng = random.Random(2050)
        self.stars = [(rng.random(), rng.random(), rng.uniform(0.4, 2.0)) for _ in range(115)]
        self.drops = [(rng.random(), rng.random(), rng.uniform(6, 19)) for _ in range(78)]
        self.timer = QTimer(self)
        self.timer.setInterval(70)
        self.timer.timeout.connect(self._next_frame)
        self._update_timer()

    def set_visuals(self, name: str, reduce_motion: bool, mode: str = "light", intensity: int = 48):
        self.theme_name = name if name in THEMES else "daybreak"
        self.reduce_motion = bool(reduce_motion)
        self.mode = mode if mode in MODES else "light"
        self.intensity = max(0, min(100, int(intensity)))
        self._update_timer()
        self.update()

    def _update_timer(self):
        if self.isVisible() and not self.reduce_motion and self.intensity > 0 and THEMES[self.theme_name].scene != "minimal":
            if not self.timer.isActive():
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
        self.phase = (self.phase + .005 + .007 * self.intensity/100) % 1.0
        self.update()

    def paintEvent(self, event):
        w, h = self.width(), self.height()
        if w < 2 or h < 2:
            return
        theme = THEMES[self.theme_name]
        colors = palette_for(self.theme_name, self.mode)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg = QLinearGradient(0, 0, w, h)
        if self.mode == "fusion":
            bg.setColorAt(0, QColor(colors.base))
            bg.setColorAt(.56, QColor(colors.top))
            bg.setColorAt(1, QColor(colors.base))
        else:
            bg.setColorAt(0, QColor(colors.base))
            bg.setColorAt(.63, QColor(colors.top))
            bg.setColorAt(1, QColor(colors.base))
        painter.fillRect(self.rect(), bg)
        if theme.scene == "minimal":
            painter.end()
            return
        opacity = (self.intensity / 100) * (0.38 if self.mode == "light" else 0.65)
        self._glow(painter, w*.82, h*.25, min(w,h)*.58, theme.second, int(80*opacity))
        self._glow(painter, w*.18, h*.85, min(w,h)*.70, theme.accent, int(55*opacity))
        painter.setOpacity(.28 + opacity*.85)
        if theme.scene in ("orbit", "nebula"):
            self._space(painter, w, h, theme)
        elif theme.scene in ("rain",):
            self._rain(painter, w, h, theme)
        elif theme.scene == "ocean":
            self._waves(painter, w, h, theme)
        elif theme.scene in ("bloom", "leaf"):
            self._petals(painter, w, h, theme)
        else:
            self._sky(painter, w, h, theme)
        painter.end()

    @staticmethod
    def _glow(painter, x, y, radius, color, opacity):
        grad = QRadialGradient(x, y, radius)
        a = QColor(color)
        a.setAlpha(max(0, min(255, opacity)))
        grad.setColorAt(0, a)
        a.setAlpha(0)
        grad.setColorAt(1, a)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(grad)
        painter.drawEllipse(int(x-radius), int(y-radius), int(radius*2), int(radius*2))

    def _space(self, painter, w, h, theme):
        painter.setPen(Qt.PenStyle.NoPen)
        for x,y,r in self.stars:
            lum = .5 + .35*math.sin((x+y+self.phase)*math.tau)
            shade = QColor("#FFFFFF") if self.mode == "dark" else QColor(theme.accent)
            shade.setAlpha(int(max(20, min(220, 180*lum))))
            painter.setBrush(shade)
            painter.drawEllipse(int(x*w), int(y*h), max(1,int(r)), max(1,int(r)))
        if theme.scene == "orbit":
            cx,cy,r = w*.83,h*.52,min(w,h)*.22
            g=QRadialGradient(cx-r*.26,cy-r*.24,r*1.6)
            g.setColorAt(0,QColor("#A9EDFC"));g.setColorAt(.35,QColor("#4EA9D8"));g.setColorAt(1,QColor("#35518C"))
            painter.setBrush(g)
            painter.setPen(QPen(QColor(theme.second), 2))
            painter.drawEllipse(int(cx-r),int(cy-r),int(2*r),int(2*r))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(theme.accent), 2))
            painter.drawArc(int(cx-r*1.42),int(cy-r*.59),int(r*2.84),int(r*1.18),int(self.phase*5760),1400)

    def _rain(self,painter,w,h,theme):
        painter.setPen(QPen(QColor(theme.accent),1.3))
        for x,y,length in self.drops:
            yy=((y+self.phase*2.6)%1)*h
            painter.drawLine(int(x*w),int(yy),int(x*w-4),int(yy+length))

    def _waves(self,painter,w,h,theme):
        for n in range(11):
            ypos=h*(.37+n*.06)
            col=QColor(theme.accent if n%2 else theme.second)
            col.setAlpha(160-n*9)
            painter.setPen(QPen(col,1.6))
            last=None
            for x in range(0,w+20,14):
                y=ypos+math.sin(x/max(w,1)*14+n*.6+self.phase*math.tau)*(7+n*.3)
                if last:painter.drawLine(last[0],int(last[1]),x,int(y))
                last=(x,y)

    def _petals(self,painter,w,h,theme):
        painter.setPen(Qt.PenStyle.NoPen)
        for i,(x,y,r) in enumerate(self.stars[:52]):
            yy=((y+self.phase*.24*(.4+r))%1)*h
            painter.setBrush(QColor(theme.second if i%3 else theme.accent))
            painter.drawEllipse(int(x*w+math.sin(self.phase*math.tau+i)*13),int(yy),int(r*3+2),int(r*4+3))

    def _sky(self,painter,w,h,theme):
        cx=w*.84;cy=h*.42;r=min(w,h)*.145
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme.second))
        painter.drawEllipse(int(cx-r),int(cy-r),int(r*2),int(r*2))
        for x,y,r0 in self.stars[:20]:
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawEllipse(int(x*w),int(y*h),int(r0*2+2),int(r0*2+2))


class VisualPreferences:
    """Settings are local device preferences; never stored with clinical data."""

    def __init__(self):
        self.settings=QSettings("TRUY TINH", "AETHERION")
        t=str(self.settings.value("visual/theme","daybreak"))
        self.theme_name=t if t in THEMES else "daybreak"
        m=str(self.settings.value("visual/mode","light"))
        self.mode=m if m in MODES else "light"
        lang=str(self.settings.value("ui/language","vi"))
        self.language=lang if lang in LANGUAGES else "vi"
        family=str(self.settings.value("visual/font_family","Segoe UI"))
        self.font_family=family if family in FONTS else "Segoe UI"
        self.font_size=self._clamp(self.settings.value("visual/font_size",10),9,15,10)
        self.animation_intensity=self._clamp(self.settings.value("visual/animation_intensity",48),0,100,48)
        self.reduce_motion=str(self.settings.value("visual/reduce_motion","false")).lower()=="true"
        self.high_contrast=str(self.settings.value("visual/high_contrast","false")).lower()=="true"
        override=str(self.settings.value("visual/accent_override",""))
        self.accent_override=override if QColor(override).isValid() else ""

    @staticmethod
    def _clamp(value, minimum, maximum, fallback):
        try:return max(minimum,min(maximum,int(value)))
        except (TypeError,ValueError):return fallback

    def _write(self,key,value):
        self.settings.setValue(key,value)

    def set_theme(self,name):
        if name in THEMES:self.theme_name=name;self._write("visual/theme",name)

    def set_mode(self,mode):
        if mode in MODES:self.mode=mode;self._write("visual/mode",mode)

    def set_language(self,language):
        if language in LANGUAGES:self.language=language;self._write("ui/language",language)

    def set_font_family(self,family):
        if family in FONTS:self.font_family=family;self._write("visual/font_family",family)

    def set_font_size(self,size):
        self.font_size=self._clamp(size,9,15,10);self._write("visual/font_size",self.font_size)

    def set_animation_intensity(self,intensity):
        self.animation_intensity=self._clamp(intensity,0,100,48);self._write("visual/animation_intensity",self.animation_intensity)

    def set_reduced_motion(self,on):
        self.reduce_motion=bool(on);self._write("visual/reduce_motion",on)

    def set_high_contrast(self,on):
        self.high_contrast=bool(on);self._write("visual/high_contrast",on)

    def set_accent_override(self,color):
        if color and not QColor(color).isValid():
            return
        self.accent_override=color
        self._write("visual/accent_override",color)

    def reset(self):
        for key in ("visual/theme","visual/mode","visual/font_family","visual/font_size",
                    "visual/animation_intensity","visual/reduce_motion","visual/high_contrast","ui/language","visual/accent_override"):
            self.settings.remove(key)
        self.__init__()

    def apply(self,app):
        app.setFont(QFont(self.font_family,self.font_size))
        app.setStyleSheet(make_stylesheet(palette_for(self.theme_name,self.mode,self.high_contrast,self.accent_override),self.font_family,self.high_contrast))


def make_stylesheet(p: Palette, family="Segoe UI", high_contrast=False) -> str:
    """One consistent source for Portal, Mission, personal health and Library."""
    style=r'''
    QMainWindow, QWidget { color:%(text)s; font-family:"%(font)s"; }
    QMainWindow, QWidget#appRoot, QStackedWidget#pageStack {background:%(base)s;}
    QFrame#topBar {background:%(header)s; border-bottom:1px solid %(border)s;}
    QFrame#footerBar {background:%(header)s; border-top:1px solid %(border)s;}
    QLabel {background:transparent; color:%(text)s;}
    QLabel#eyebrow, QLabel#cardNumber {color:%(accent)s; font-size:11px; font-weight:700; letter-spacing:1px;}
    QLabel#heroTitle {font-size:37px; font-weight:800; color:%(text)s;}
    QLabel#heroCopy {color:%(muted)s; font-size:15px;}
    QLabel#pageHint, QLabel#cardDescription, QLabel#detail {color:%(muted)s; font-size:13px;}
    QLabel#heading {font-size:27px; font-weight:750; color:%(text)s;}
    QLabel#connectionPill {background:%(surface)s; color:%(muted)s; border:1px solid %(border)s; border-radius:14px; padding:7px 12px;}
    QFrame#portalCard {background:%(card)s; border:1px solid %(border)s; border-radius:21px;}
    QFrame#portalCard:hover {background:%(card_hover)s; border:2px solid %(accent)s;}
    QFrame#surface, QFrame#contentPanel, QFrame#settingsCard {background:%(surface)s; border:1px solid %(border)s; border-radius:18px;}
    QPushButton, QToolButton {background:%(surface)s; color:%(text)s; border:1px solid %(border)s; border-radius:11px; padding:9px 13px; min-height:26px;}
    QPushButton:hover, QToolButton:hover {border-color:%(accent)s; background:%(surface_alt)s;}
    QPushButton:focus, QToolButton:focus {border:2px solid %(accent)s;}
    QPushButton:checked, QToolButton:checked {background:%(accent)s; color:%(on_accent)s; border:1px solid %(accent)s;}
    QPushButton#brandButton {background:transparent; border:0; font-size:18px; font-weight:800; letter-spacing:2px; color:%(header_text)s; padding:6px 0;}
    QPushButton#navButton {background:transparent; border:0; font-size:12px; font-weight:600; padding:8px 9px; color:%(header_text)s;}
    QPushButton#navButton:hover {background:%(surface_alt)s; color:%(text)s; border-radius:9px;}
    QPushButton#portalCardButton {background:transparent; border:0; padding:0; text-align:left; font-weight:750; font-size:20px; min-height:36px;}
    QPushButton#portalCardButton:hover {color:%(accent)s;}
    QPushButton#primaryAction {background:%(accent)s; color:%(on_accent)s; border:0; font-weight:750;}
    QPushButton#primaryAction:hover {background:%(second)s;}
    QToolButton#headerAction {background:transparent; border:1px solid %(border)s; color:%(header_text)s; padding:9px 10px;}
    QToolButton#headerAction:hover {background:%(surface_alt)s; color:%(text)s;}
    QTableWidget, QTableView, QListView, QTreeView {background:%(surface)s; alternate-background-color:%(surface_alt)s; color:%(text)s; border:1px solid %(border)s; gridline-color:%(border)s; selection-background-color:%(top)s;}
    QHeaderView::section {background:%(surface_alt)s; color:%(text)s; border:0; border-bottom:1px solid %(border)s; padding:9px;}
    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QSpinBox {background:%(surface)s; border:1px solid %(border)s; border-radius:9px; padding:8px; color:%(text)s;}
    QMenu {background:%(surface)s; border:1px solid %(border)s; padding:7px; color:%(text)s;}
    QMenu::item {padding:10px 25px; border-radius:7px;}
    QMenu::item:selected {background:%(surface_alt)s;}
    QTabWidget::pane {border:0; background:transparent;}
    QTabBar::tab {background:%(surface_alt)s; border:1px solid %(border)s; border-radius:11px; padding:11px 17px; margin:0 3px 0 0; color:%(muted)s;}
    QTabBar::tab:selected {background:%(surface)s; color:%(accent)s; border-bottom:2px solid %(accent)s;}
    QScrollArea, QScrollArea QWidget#qt_scrollarea_viewport {background:transparent; border:0;}
    QScrollBar:vertical {background:transparent; width:10px;}
    QScrollBar::handle:vertical {background:%(border)s; border-radius:5px; min-height:25px;}
    QSlider::groove:horizontal {height:7px; background:%(border)s; border-radius:3px;}
    QSlider::handle:horizontal {background:%(accent)s; width:17px; margin:-5px 0; border-radius:8px;}
    QCheckBox {spacing:9px; padding:5px;}
    QCheckBox::indicator {width:18px; height:18px;}
    '''
    return style % {
        "base":p.base,"top":p.top,"surface":p.surface,"surface_alt":p.surface_alt,
        "border":p.border,"accent":p.accent,"second":p.second,"text":p.text,
        "muted":p.muted,"header":p.header,"header_text":p.header_text,
        "card":p.card,"card_hover":p.card_hover,"on_accent":p.on_accent,
        "font":family.replace('"','')
    }
