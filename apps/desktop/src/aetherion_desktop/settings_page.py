"""AETHERION D62: native, interactive, horizontal-tab Settings and living garden.

The scene is original Qt vector art painted in the UI; it never queries a web
service or displays invented health data. Server-side settings are not faked.
"""
from __future__ import annotations

import math
import random

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QColorDialog, QComboBox, QDialog, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea,
    QSizePolicy, QSlider, QTabWidget, QVBoxLayout, QWidget,
)

from .localize import tr
from .visual_theme import FONTS, THEMES, VisualPreferences, _hex, _mix, palette_for


class OwlGarden(QWidget):
    """A tiny illustrated ecosystem: animated tree, owl blink, sun/moon and leaves."""

    def __init__(self, prefs: VisualPreferences, parent=None):
        super().__init__(parent)
        self.preferences = prefs
        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.phase = 0.0
        self.daylight = {'light': 1.0, 'dark': 0.0, 'fusion': .52}[prefs.mode]
        self.target = self.daylight
        rng = random.Random(1045)
        self.leaves = [(rng.uniform(0, 1), rng.uniform(0, 1), rng.uniform(2, 9)) for _ in range(45)]
        self.stars = [(rng.uniform(25, 770), rng.uniform(30, 235), rng.uniform(1, 2.7)) for _ in range(42)]
        self.timer = QTimer(self)
        self.timer.setInterval(45)
        self.timer.timeout.connect(self._frame)
        self._update_timer()

    def set_preferences(self, prefs: VisualPreferences):
        self.preferences = prefs
        self.target = {'light': 1.0, 'dark': 0.0, 'fusion': .52}[prefs.mode]
        if prefs.reduce_motion:
            self.daylight = self.target
        self._update_timer()
        self.update()

    def _update_timer(self):
        animate = not self.preferences.reduce_motion and self.preferences.animation_intensity > 0 and self.isVisible()
        if animate and not self.timer.isActive():
            self.timer.start()
        elif not animate:
            self.timer.stop()

    def showEvent(self, e):
        super().showEvent(e)
        self._update_timer()

    def hideEvent(self, e):
        self.timer.stop()
        super().hideEvent(e)

    def _frame(self):
        delta = self.target - self.daylight
        self.daylight = self.target if abs(delta) < .007 else self.daylight + delta*.12
        self.phase = (self.phase + .015 + .06*self.preferences.animation_intensity/100) % (math.tau*400)
        self.update()

    def paintEvent(self, e):
        if self.width() < 5 or self.height() < 5:
            return
        w, h = float(self.width()), float(self.height())
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Keep fixed art proportions, scale to window; no raster images or licenses.
        p.scale(w/800, h/470)
        clip = QPainterPath()
        clip.addRoundedRect(0., 0., 800., 470., 28., 28.)
        p.setClipPath(clip)
        d = self.daylight
        theme = THEMES[self.preferences.theme_name]
        sky = QLinearGradient(0., 0., 0., 470.)
        sky.setColorAt(0, _mix('#16264B', '#79C9F4', d))
        sky.setColorAt(.60, _mix('#3A416D', '#E7F6FA', d))
        sky.setColorAt(1, _mix('#7F718A', '#FFEDCF', d))
        p.fillRect(0, 0, 800, 470, sky)
        # Night sky fades as sun rises.
        p.setPen(Qt.PenStyle.NoPen)
        for x,y,r in self.stars:
            c=QColor('#FFFDF4');c.setAlpha(int((1-d)*215))
            p.setBrush(c);p.drawEllipse(int(x),int(y),int(r*2),int(r*2))
        sun = QColor('#FFE2A4');sun.setAlpha(int(245*d))
        p.setBrush(sun);p.drawEllipse(603,56,100,100)
        moon = QColor('#FDF2D5');moon.setAlpha(int(240*(1-d)))
        p.setBrush(moon);p.drawEllipse(615,65,77,77)
        crater=QColor('#B9BDD8');crater.setAlpha(int(100*(1-d)))
        p.setBrush(crater);p.drawEllipse(639,86,16,16);p.drawEllipse(658,115,10,10)
        # Gentle illustrated clouds, soft hills and ribbon of distant water.
        cloud=QColor('#FFFFFF');cloud.setAlpha(int(85*d+15))
        p.setBrush(cloud)
        for x,y in ((65,88),(392,122),(685,198)):
            p.drawEllipse(x,y,115,24);p.drawEllipse(x+18,y-17,59,32)
        hill = QPainterPath();hill.moveTo(0,336);hill.cubicTo(160,247,293,375,456,294)
        hill.cubicTo(595,231,695,327,800,264);hill.lineTo(800,470);hill.lineTo(0,470);hill.closeSubpath()
        p.fillPath(hill,_mix('#2A5872','#85B6A2',d))
        foreground = QPainterPath();foreground.moveTo(0,400)
        foreground.cubicTo(179,368,272,428,426,391)
        foreground.cubicTo(557,352,657,404,800,368)
        foreground.lineTo(800,470);foreground.lineTo(0,470);foreground.closeSubpath()
        p.fillPath(foreground,_mix('#24435A','#A9D6AD',d))
        p.setPen(QPen(_mix('#557D89','#E3F5E1',d),2))
        for n in range(6):
            yy=418+n*6
            p.drawArc(10,yy,780,110,-4*16,90*16)
        # Tree trunk and organic curved branches, backed by leafy clusters.
        trunk=QPainterPath();trunk.moveTo(179,480);trunk.cubicTo(212,349,183,273,203,161)
        trunk.cubicTo(221,122,234,138,240,137)
        p.setPen(QPen(_mix('#52445A','#8C694B',d),31,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        p.drawPath(trunk)
        branches=[((211,244),(143,182),(108,127)),((213,196),(296,156),(365,116)),
                  ((209,317),(293,292),(426,267)),((225,150),(180,83),(158,67))]
        p.setPen(QPen(_mix('#52445A','#80664E',d),12,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
        for start,mid,end in branches:
            path=QPainterPath();path.moveTo(*start);path.quadTo(*mid,*end);p.drawPath(path)
        # Foliage follows the scene, bright greens by day, teal/purple by night.
        clusters=[(128,140,107),(240,101,106),(328,154,86),(91,232,79),(299,229,71),(396,181,68)]
        for i,(x,y,r) in enumerate(clusters):
            base = _mix('#315978','#72B78B' if i%2 else '#A0CF90',d)
            base = _mix(base,theme.second,.15)
            g=QRadialGradient(x-r*.23,y-r*.28,r*1.12)
            g.setColorAt(0,_mix(base,'#FFFFFF',.24*d));g.setColorAt(1,_mix(base,'#152D50',.12))
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(g)
            sway = 0 if self.preferences.reduce_motion else 3*math.sin(self.phase*.70+i*.6)
            p.drawEllipse(int(x-r*.85+sway),int(y-r*.68),int(r*1.65),int(r*1.43))
        # Tiny floating leaves, only from the illustrative setting scene.
        if not self.preferences.reduce_motion:
            for i,(x,y,r) in enumerate(self.leaves):
                dx=95+(x*445)+math.sin(self.phase*.4+i)*11
                dy=((y*470+self.phase*(1+r*.04)*2) % 480)
                c=_mix('#7CB6B1','#ECD48A',d);c.setAlpha(70)
                p.setPen(Qt.PenStyle.NoPen);p.setBrush(c)
                p.drawEllipse(int(dx),int(dy),max(2,int(r*.8)),max(3,int(r*1.4)))
        # Owl perched safely on the branch, with genuine animated blinking.
        p.save()
        bob=0 if self.preferences.reduce_motion else math.sin(self.phase*.9)*2
        p.translate(418,245+bob)
        body=_mix('#465D82','#A77055',d)
        wing=_mix('#35456C','#9B5E50',d)
        belly=_mix('#C2A5B7','#F4D7AB',d)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(44,37,55,55));p.drawEllipse(-59,117,122,20)
        p.setBrush(body);p.drawEllipse(-60,-52,120,163)
        p.setBrush(belly);p.drawEllipse(-36,-15,72,108)
        p.setBrush(wing);p.drawEllipse(-60,-4,38,86);p.drawEllipse(22,-4,38,86)
        # Pointed fluffy ear-tufts.
        left=QPainterPath();left.moveTo(-47,-23);left.lineTo(-59,-92);left.quadTo(-16,-78,-4,-45);left.closeSubpath()
        right=QPainterPath();right.moveTo(47,-23);right.lineTo(59,-92);right.quadTo(16,-78,4,-45);right.closeSubpath()
        p.fillPath(left,body);p.fillPath(right,body)
        face=_mix('#D8BDCA','#F7E6C5',d)
        p.setBrush(face);p.drawEllipse(-53,-61,57,60);p.drawEllipse(-4,-61,57,60)
        eye=_mix('#C9B9FA','#FFF4B9',d)
        p.setBrush(eye);p.drawEllipse(-39,-43,29,29);p.drawEllipse(10,-43,29,29)
        # In bright daylight the owl is sleepy; night eyes are wide and awake.
        sleepy = max(0., min(.65, .55*d))
        blink = 0.0 if self.preferences.reduce_motion else max(0., math.cos(self.phase*1.8-2.4)**25)*.86
        openness = max(.06, 1.0-sleepy-blink)
        p.setBrush(QColor('#28364E'))
        p.drawEllipse(-32,int(-36+13*(1-openness)),15,max(2,int(17*openness)))
        p.drawEllipse(17,int(-36+13*(1-openness)),15,max(2,int(17*openness)))
        p.setBrush(QColor('#F4B96D'))
        nose=QPainterPath();nose.moveTo(-8,-13);nose.lineTo(8,-13);nose.lineTo(0,0);nose.closeSubpath();p.drawPath(nose)
        p.setPen(QPen(QColor('#D4A66A'),4));p.drawLine(-25,104,-29,118);p.drawLine(25,104,29,118)
        p.restore()
        # Border and tiny explanatory badge, independent of app data.
        p.setClipping(False)
        p.setPen(QPen(QColor(255,255,255,115),2));p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(1,1,798,468,27,27)
        p.end()


class SettingsPage(QWidget):
    """Real D62 Settings page. Choices persist immediately, no fake service switches."""

    preferences_changed = Signal()
    connection_test_requested = Signal()
    go_home = Signal()

    def __init__(self, prefs: VisualPreferences, server_url: str, parent=None):
        super().__init__(parent)
        self.preferences = prefs
        self.server_url = server_url
        self._syncing = False
        self._tab_keys = ('appearance','language','connection','notifications','privacy','accessibility')
        self._ui = {}
        root=QVBoxLayout(self)
        root.setContentsMargins(28,22,28,20)
        root.setSpacing(13)
        header=QHBoxLayout()
        copy=QVBoxLayout()
        self.title=QLabel();self.title.setObjectName('heroTitle')
        self.subtitle=QLabel();self.subtitle.setObjectName('heroCopy');self.subtitle.setWordWrap(True)
        copy.addWidget(self.title);copy.addWidget(self.subtitle)
        header.addLayout(copy,1)
        self.back=QPushButton();self.back.setObjectName('navButton')
        self.back.clicked.connect(self.go_home.emit)
        header.addWidget(self.back)
        root.addLayout(header)
        self.tabs=QTabWidget();self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        root.addWidget(self.tabs,1)
        self._build_appearance()
        self._build_language()
        self._build_connection()
        self._build_notifications()
        self._build_privacy()
        self._build_accessibility()
        bottom=QHBoxLayout()
        self.status=QLabel();self.status.setObjectName('pageHint')
        bottom.addWidget(self.status,1)
        self.reset_button=QPushButton();self.reset_button.clicked.connect(self._reset)
        self.apply_button=QPushButton();self.apply_button.setObjectName('primaryAction')
        self.apply_button.clicked.connect(self._apply)
        bottom.addWidget(self.reset_button);bottom.addWidget(self.apply_button)
        root.addLayout(bottom)
        self._sync()

    @staticmethod
    def _panel(parent_layout, *, vertical=True):
        frame=QFrame();frame.setObjectName('settingsCard')
        layout=(QVBoxLayout if vertical else QHBoxLayout)(frame)
        layout.setContentsMargins(18,16,18,16);layout.setSpacing(12)
        parent_layout.addWidget(frame)
        return layout

    @staticmethod
    def _scrolled(content):
        container=QScrollArea();container.setWidgetResizable(True)
        container.setFrameShape(QFrame.Shape.NoFrame)
        container.setWidget(content)
        return container

    def _build_appearance(self):
        page=QWidget();outer=QVBoxLayout(page);outer.setContentsMargins(0,12,0,0)
        split=QHBoxLayout();split.setSpacing(18);outer.addLayout(split,1)
        left=QWidget();left_layout=QVBoxLayout(left);left_layout.setContentsMargins(0,0,0,0);left_layout.setSpacing(12)
        left_scroll=self._scrolled(left);left_scroll.setMinimumWidth(390)
        split.addWidget(left_scroll,10)
        mode=self._panel(left_layout)
        self.mode_label=QLabel();self.mode_label.setObjectName('heading');mode.addWidget(self.mode_label)
        group=QHBoxLayout();mode.addLayout(group)
        self.mode_group=QButtonGroup(self);self.mode_group.setExclusive(True)
        self.mode_buttons={}
        for key in ('light','fusion','dark'):
            b=QPushButton();b.setCheckable(True);b.setMinimumHeight(46)
            b.clicked.connect(lambda checked=False, k=key:self._mode_changed(k))
            group.addWidget(b);self.mode_group.addButton(b);self.mode_buttons[key]=b
        chooser=self._panel(left_layout)
        self.themes_label=QLabel();self.themes_label.setObjectName('heading');chooser.addWidget(self.themes_label)
        self.themes_hint=QLabel();self.themes_hint.setObjectName('pageHint')
        chooser.addWidget(self.themes_hint)
        grid=QGridLayout();grid.setSpacing(8);chooser.addLayout(grid)
        self.theme_buttons={}
        for i,(key,theme) in enumerate(THEMES.items()):
            b=QPushButton('●  '+theme.title)
            b.setObjectName('themeChip');b.setCheckable(True);b.setMinimumHeight(35)
            b.clicked.connect(lambda checked=False,k=key:self._theme_changed(k))
            grid.addWidget(b,i//2,i%2);self.theme_buttons[key]=b
        tint_row=QHBoxLayout();chooser.addLayout(tint_row)
        self.accent_button=QPushButton();self.accent_button.clicked.connect(self._select_accent)
        self.accent_reset=QPushButton('↻');self.accent_reset.clicked.connect(lambda:self._accent_changed(''))
        tint_row.addWidget(self.accent_button,1);tint_row.addWidget(self.accent_reset)
        movement=self._panel(left_layout)
        self.motion_label=QLabel();self.motion_label.setObjectName('heading');movement.addWidget(self.motion_label)
        self.motion_slider=QSlider(Qt.Orientation.Horizontal)
        self.motion_slider.setRange(0,100);self.motion_slider.setTickInterval(25)
        self.motion_slider.valueChanged.connect(self._animation_changed)
        movement.addWidget(self.motion_slider)
        self.reduce_check=QCheckBox();self.reduce_check.toggled.connect(self._reduce_changed)
        movement.addWidget(self.reduce_check)
        left_layout.addStretch(1)
        right=QFrame();right.setObjectName('settingsCard')
        right_layout=QVBoxLayout(right);right_layout.setContentsMargins(17,17,17,17)
        right_layout.setSpacing(11)
        self.scene_heading=QLabel();self.scene_heading.setObjectName('heading')
        self.scene_copy=QLabel();self.scene_copy.setObjectName('pageHint');self.scene_copy.setWordWrap(True)
        right_layout.addWidget(self.scene_heading);right_layout.addWidget(self.scene_copy)
        self.garden=OwlGarden(self.preferences)
        right_layout.addWidget(self.garden,1)
        self.scene_caption=QLabel();self.scene_caption.setObjectName('eyebrow')
        right_layout.addWidget(self.scene_caption)
        self.preview_button=QPushButton();self.preview_button.clicked.connect(self._full_preview)
        right_layout.addWidget(self.preview_button)
        split.addWidget(right,11)
        self.tabs.addTab(page,'')

    def _build_language(self):
        page=QWidget();col=QVBoxLayout(page);col.setContentsMargins(25,25,25,25)
        panel=self._panel(col)
        self.language_label=QLabel();self.language_label.setObjectName('heading');panel.addWidget(self.language_label)
        self.lang_combo=QComboBox();self.lang_combo.addItem('Tiếng Việt','vi');self.lang_combo.addItem('English','en')
        self.lang_combo.currentIndexChanged.connect(self._language_changed)
        panel.addWidget(self.lang_combo)
        self.lang_hint=QLabel();self.lang_hint.setWordWrap(True);self.lang_hint.setObjectName('pageHint')
        panel.addWidget(self.lang_hint)
        col.addStretch();self.tabs.addTab(page,'')

    def _build_connection(self):
        page=QWidget();col=QVBoxLayout(page);col.setContentsMargins(25,25,25,25)
        panel=self._panel(col)
        self.connection_title=QLabel();self.connection_title.setObjectName('heading');panel.addWidget(self.connection_title)
        self.server_label=QLabel();panel.addWidget(self.server_label)
        self.server_input=QLineEdit(self.server_url);self.server_input.setReadOnly(True)
        self.server_input.setAccessibleName('Current active AETHERION HTTP Server endpoint')
        panel.addWidget(self.server_input)
        self.connection_hint=QLabel();self.connection_hint.setObjectName('pageHint')
        self.connection_hint.setWordWrap(True);panel.addWidget(self.connection_hint)
        self.connection_button=QPushButton();self.connection_button.clicked.connect(self.connection_test_requested.emit)
        panel.addWidget(self.connection_button)
        col.addStretch();self.tabs.addTab(page,'')

    def _info_tab(self,description_key):
        page=QWidget();col=QVBoxLayout(page);col.setContentsMargins(25,25,25,25)
        panel=self._panel(col)
        title=QLabel();title.setObjectName('heading');panel.addWidget(title)
        message=QLabel();message.setWordWrap(True);message.setObjectName('pageHint');panel.addWidget(message)
        col.addStretch()
        self._ui[description_key]=(title,message)
        self.tabs.addTab(page,'')

    def _build_notifications(self):self._info_tab('notifications')
    def _build_privacy(self):self._info_tab('privacy')

    def _build_accessibility(self):
        page=QWidget();col=QVBoxLayout(page);col.setContentsMargins(25,25,25,25)
        panel=self._panel(col)
        self.access_title=QLabel();self.access_title.setObjectName('heading');panel.addWidget(self.access_title)
        self.font_label=QLabel();panel.addWidget(self.font_label)
        self.font_combo=QComboBox()
        for family in ('Segoe UI','Arial','Noto Sans','Inter','Roboto'):
            self.font_combo.addItem(family,family)
        self.font_combo.currentIndexChanged.connect(self._font_changed)
        panel.addWidget(self.font_combo)
        self.fontsize_label=QLabel();panel.addWidget(self.fontsize_label)
        self.font_slider=QSlider(Qt.Orientation.Horizontal);self.font_slider.setRange(9,15)
        self.font_slider.valueChanged.connect(self._fontsize_changed)
        panel.addWidget(self.font_slider)
        self.contrast_check=QCheckBox();self.contrast_check.toggled.connect(self._contrast_changed)
        self.reduce_check_access=QCheckBox();self.reduce_check_access.toggled.connect(self._reduce_changed)
        panel.addWidget(self.contrast_check);panel.addWidget(self.reduce_check_access)
        self.access_hint=QLabel();self.access_hint.setObjectName('pageHint');self.access_hint.setWordWrap(True)
        panel.addWidget(self.access_hint)
        col.addStretch();self.tabs.addTab(page,'')

    def _change(self):
        if self._syncing:return
        self.preferences_changed.emit()
        self._sync()
        self.status.setText(tr('saved_msg',self.preferences.language))

    def _mode_changed(self, mode):
        if self._syncing: return
        self.preferences.set_mode(mode);self._change()

    def _theme_changed(self, name):
        if self._syncing: return
        self.preferences.set_theme(name);self._change()

    def _accent_changed(self, color):
        if self._syncing: return
        self.preferences.set_accent_override(color);self._change()

    def _select_accent(self):
        initial=self.preferences.accent_override or THEMES[self.preferences.theme_name].accent
        choice=QColorDialog.getColor(QColor(initial),self,tr('theme',self.preferences.language))
        if choice.isValid():self._accent_changed(choice.name())

    def _animation_changed(self, value):
        if self._syncing: return
        self.preferences.set_animation_intensity(value);self._change()

    def _reduce_changed(self, value):
        if self._syncing: return
        self.preferences.set_reduced_motion(value);self._change()

    def _contrast_changed(self, value):
        if self._syncing: return
        self.preferences.set_high_contrast(value);self._change()

    def _fontsize_changed(self, value):
        if self._syncing: return
        self.preferences.set_font_size(value);self._change()

    def _font_changed(self, index):
        if self._syncing: return
        font=self.font_combo.currentData()
        if font:self.preferences.set_font_family(font);self._change()

    def _language_changed(self, index):
        if self._syncing: return
        lang=self.lang_combo.currentData()
        if lang:self.preferences.set_language(lang);self._change()

    def _apply(self):
        self.preferences_changed.emit()
        self.status.setText(tr('saved_msg',self.preferences.language))

    def _reset(self):
        self.preferences.reset();self.preferences_changed.emit();self._sync()

    def _full_preview(self):
        dialog=QDialog(self);dialog.setWindowTitle(tr('preview',self.preferences.language))
        dialog.resize(940,590)
        lay=QVBoxLayout(dialog)
        garden=OwlGarden(self.preferences,dialog)
        lay.addWidget(garden,1)
        close=QPushButton('Đóng' if self.preferences.language=='vi' else 'Close')
        close.clicked.connect(dialog.accept);lay.addWidget(close)
        dialog.exec()

    def _sync(self):
        self._syncing=True
        try:
            lang=self.preferences.language
            self.title.setText(tr('settings_title',lang))
            self.subtitle.setText(tr('settings_subtitle',lang))
            self.back.setText('← '+tr('back',lang))
            for i,key in enumerate(self._tab_keys):self.tabs.setTabText(i,tr(key,lang))
            self.mode_label.setText(tr('mode',lang))
            for key,b in self.mode_buttons.items():
                b.setText(('☀  ' if key=='light' else '◐  ' if key=='fusion' else '☾  ')+tr(key,lang))
                b.setChecked(key==self.preferences.mode)
            self.themes_label.setText(tr('theme',lang));self.themes_hint.setText(tr('theme_selector',lang))
            for key,b in self.theme_buttons.items():
                b.setChecked(key==self.preferences.theme_name)
                accent=THEMES[key].accent
                b.setStyleSheet(f'QPushButton {{ text-align:left; padding:8px 10px; border-left:5px solid {accent}; }}')
            self.accent_button.setText(('Màu nhấn tùy chọn' if lang=='vi' else 'Custom accent color')+'  ●')
            self.motion_label.setText(tr('animation',lang))
            self.reduce_check.setText(tr('motion_reduce',lang))
            self.reduce_check.setChecked(self.preferences.reduce_motion)
            self.motion_slider.setValue(self.preferences.animation_intensity)
            self.scene_heading.setText(tr('scene_title',lang));self.scene_copy.setText(tr('scene_desc',lang))
            self.scene_caption.setText(tr('sun' if self.preferences.mode=='light' else 'moon' if self.preferences.mode=='dark' else 'twilight',lang))
            self.preview_button.setText('↗  '+tr('preview',lang))
            self.garden.set_preferences(self.preferences)
            self.language_label.setText(tr('language',lang));self.lang_hint.setText(tr('language_hint',lang))
            self.lang_combo.setCurrentIndex(0 if lang=='vi' else 1)
            self.connection_title.setText(tr('connection',lang));self.server_label.setText(tr('server_address',lang))
            self.connection_hint.setText(tr('connection_hint',lang));self.connection_button.setText(tr('check_server',lang))
            for key in ('notifications','privacy'):
                title,message=self._ui[key];title.setText(tr(key,lang));message.setText(tr(key+'_hint',lang))
            self.access_title.setText(tr('accessibility',lang))
            self.font_label.setText(tr('font',lang));self.fontsize_label.setText(f"{tr('font_size',lang)}  ·  {self.preferences.font_size} pt")
            self.font_combo.setCurrentIndex(self.font_combo.findData(self.preferences.font_family))
            self.font_slider.setValue(self.preferences.font_size)
            self.contrast_check.setText(tr('contrast',lang));self.contrast_check.setChecked(self.preferences.high_contrast)
            self.reduce_check_access.setText(tr('motion_reduce',lang));self.reduce_check_access.setChecked(self.preferences.reduce_motion)
            self.access_hint.setText(tr('access_hint',lang));self.reset_button.setText(tr('reset',lang))
            self.apply_button.setText('✓  '+tr('apply',lang))
        finally:
            self._syncing=False

    def retranslate(self):
        self._sync()
