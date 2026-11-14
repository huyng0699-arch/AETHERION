"""AETHERION NASA hackathon replay: real, archived, explicitly non-live data.

The bundled Mercury-Atlas 7 values were transcribed from the unclassified
NASA Manned Spacecraft Center June 15 1962 report, specified table/page labels.
No unauthorized health record, fake ECG or imagined NASA telemetry is generated.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from urllib.parse import urlsplit

DATASET_ID = "NASA-MA7-MERCURY-1962"
EXPECTED_GROUPS = ("flight", "clinical", "blood", "pressure")


def load_real_nasa_data(path: str | Path | None = None) -> dict:
    """Load bundled actual numeric NASA values, fail closed if schema is corrupt."""
    target = Path(path) if path is not None else Path(__file__).with_name("ma7_source.json")
    if target.stat().st_size > 150_000:
        raise ValueError("Oversized NASA source file")
    doc = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("dataset_id") != DATASET_ID:
        raise ValueError("Wrong NASA source identity")
    if doc.get("schema_version") != "1.0.0":
        raise ValueError("Unknown NASA data schema")
    if doc.get("is_synthetic") is not False or doc.get("is_live") is not False:
        raise ValueError("Historical research must not be live or synthetic")
    url = urlsplit(str(doc.get("source_url", "")))
    if url.scheme != "https" or url.hostname not in ("nasa.gov", "www.nasa.gov"):
        raise ValueError("Missing official primary NASA source")
    groups = doc.get("groups")
    metric_names = doc.get("metric_names")
    if (not isinstance(groups, list) or len(groups) != 4 or
            any(not isinstance(g, dict) for g in groups) or
            [g["id"] for g in groups] != list(EXPECTED_GROUPS)):
        raise ValueError("Four original NASA source groups required")
    if (not isinstance(metric_names, dict) or len(metric_names) < 12 or
            any(not isinstance(v, dict) or
                not all(isinstance(v.get(loc), str) and v[loc] for loc in ("vi", "en"))
                for v in metric_names.values())):
        raise ValueError("No metric dictionary")
    for group in groups:
        if (not isinstance(group.get("title"), dict) or
                not isinstance(group.get("note"), dict) or
                any(not isinstance(group[field].get(loc), str) or
                        not group[field][loc]
                        for field in ("title", "note") for loc in ("vi", "en"))):
            raise ValueError("Missing bilingual NASA provenance description")
        records = group.get("records")
        if not group.get("table") or not isinstance(records, list) or not records:
            raise ValueError("Unprovenanced or empty NASA data section")
        seen = set()
        for row in records:
            if not isinstance(row, dict):
                raise ValueError("Invalid NASA historical record")
            rid = row.get("id")
            if not isinstance(rid, str) or rid in seen:
                raise ValueError("Missing or duplicate timepoint")
            seen.add(rid)
            title, measures = row.get("title"), row.get("measures")
            if not isinstance(title, dict) or not all(title.get(x) for x in ("vi", "en")):
                raise ValueError("Missing original timepoint label")
            if not isinstance(measures, dict) or not measures:
                raise ValueError("No NASA recorded observations")
            for metric_id, observed in measures.items():
                if metric_id not in metric_names or not isinstance(observed, dict):
                    raise ValueError("Unknown NASA indicator")
                val = observed.get("value")
                if val is None and not observed.get("missing"):
                    raise ValueError("Missing NASA measurement not labelled")
                if isinstance(val, (float, int)) and (isinstance(val, bool) or not math.isfinite(val)):
                    raise ValueError("Invalid NASA numeric measurement")
                if val is not None and (not isinstance(val, (float, int, str)) or not str(val)):
                    raise ValueError("Invalid NASA archived value")
                if not isinstance(observed.get("unit"), str) or not observed["unit"]:
                    raise ValueError("Missing NASA source unit")
    return doc


def measured_points(records: list[dict], metric_id: str) -> tuple[float | None, ...]:
    """Return only individually reported numeric values; never interpolate."""
    values = []
    for row in records:
        metric = row.get("measures", {}).get(metric_id)
        value = metric.get("value") if isinstance(metric, dict) else None
        values.append(float(value) if isinstance(value, (float, int)) and not isinstance(value, bool) else None)
    return tuple(values)


def build_hackathon_demo(parent=None, **kwargs):
    """Create native QWidget lazily, keeping schema readable without Qt."""
    from PySide6.QtCore import Qt, QTimer, Signal, QRectF
    from PySide6.QtGui import QDesktopServices, QColor, QPainter, QPen
    from PySide6.QtWidgets import (
        QAbstractItemView, QFrame, QGridLayout, QHBoxLayout, QHeaderView,
        QLabel, QListWidget, QProgressBar, QPushButton, QScrollArea,
        QStackedWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
    )
    from ...localization import tr, normalize_locale
    from ...visual_theme import palette_for
    from ...knowledge_browser import KnowledgeOrb

    class HistoricalBars(QWidget):
        """Selectable source-derived bars. Deliberately no continuous fake line."""
        chosen = Signal(int)

        def __init__(self):
            super().__init__()
            self.setMinimumHeight(154)
            self.setObjectName("archiveChart")
            self.points = ()
            self.theme = "daybreak"
            self.mode = "light"

        def set_series(self, points, theme, mode):
            self.points = tuple(points)
            self.theme, self.mode = theme, mode
            self.update()

        def paintEvent(self, event):
            w, h = self.width(), self.height()
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            p = palette_for(self.theme, self.mode)
            painter.setPen(QPen(QColor(p.border), 1))
            painter.drawLine(22, h-29, w-15, h-29)
            numeric = [n for n in self.points if n is not None]
            if not numeric:
                painter.end()
                return
            lo, hi = min(numeric), max(numeric)
            span = hi-lo if hi != lo else max(abs(hi)*.12, 1)
            count = len(self.points)
            gap = max(36.0, (w-48)/max(count, 1))
            for i, val in enumerate(self.points):
                x = 25 + (i+.5)*gap
                if val is not None:
                    bar_height = 35 + 75 * (val-lo)/span
                    painter.setPen(Qt.PenStyle.NoPen)
                    fill = QColor(p.accent if i % 2 == 0 else p.second)
                    fill.setAlpha(185)
                    painter.setBrush(fill)
                    painter.drawRoundedRect(QRectF(x-gap*.20, h-29-bar_height,
                                                  gap*.40, bar_height), 5, 5)
                    painter.setPen(QPen(QColor(p.text), 1))
                    painter.drawText(QRectF(x-gap*.45, h-28-bar_height, gap*.9, 22),
                                     Qt.AlignmentFlag.AlignCenter, f"{val:g}")
                painter.setPen(QPen(QColor(p.muted), 1))
                painter.drawText(QRectF(x-gap*.45, h-25, gap*.9, 18),
                                 Qt.AlignmentFlag.AlignCenter, str(i+1))
            painter.end()

        def mouseReleaseEvent(self, event):
            if self.points and event.button() == Qt.MouseButton.LeftButton:
                gap = max(36.0, (self.width()-48)/max(len(self.points),1))
                index = round((event.position().x()-25)/gap-.5)
                if 0 <= index < len(self.points):
                    self.chosen.emit(index)
            super().mouseReleaseEvent(event)

    class NasaHackathonDemo(QWidget):
        home_requested = Signal()

        def __init__(self):
            super().__init__(parent)
            self.language = normalize_locale(kwargs.get("locale", "vi"))
            self.theme = kwargs.get("theme", "daybreak")
            self.mode = kwargs.get("mode", "light")
            self.reduce_motion = bool(kwargs.get("reduce_motion", False))
            self.intensity = int(kwargs.get("intensity", 48))
            self.doc = None
            self.group_index = 0
            self.group = None
            self.record = None

            self.root = QVBoxLayout(self)
            self.root.setContentsMargins(0, 0, 0, 0)
            self.pages = QStackedWidget()
            self.root.addWidget(self.pages)
            self._build_briefing()
            self._build_replay()
            self.timer = QTimer(self)
            self.timer.setInterval(2400)
            self.timer.timeout.connect(self.next_stage)
            self.set_locale(self.language)
            self.pages.setCurrentWidget(self.briefing)

        def t(self, key: str, **parts):
            return tr(self.language, "demo." + key, **parts)

        def _scroll_page(self, minimum=0):
            page = QWidget()
            shell = QVBoxLayout(page)
            shell.setContentsMargins(0, 0, 0, 0)
            area = QScrollArea(page)
            area.setWidgetResizable(True)
            area.setFrameShape(QFrame.Shape.NoFrame)
            area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            shell.addWidget(area)
            surface = QWidget()
            if minimum:
                surface.setMinimumWidth(minimum)
            area.setWidget(surface)
            body = QVBoxLayout(surface)
            body.setContentsMargins(34, 24, 34, 26)
            body.setSpacing(17)
            return page, body

        def _build_briefing(self):
            self.briefing, body = self._scroll_page()
            hero = QFrame()
            hero.setObjectName("contentPanel")
            row = QHBoxLayout(hero)
            row.setContentsMargins(27, 18, 25, 19)
            headings = QVBoxLayout()
            headings.setSpacing(10)
            self.brief_kicker = QLabel()
            self.brief_kicker.setObjectName("eyebrow")
            headings.addWidget(self.brief_kicker)
            self.brief_title = QLabel()
            self.brief_title.setObjectName("heroTitle")
            self.brief_title.setWordWrap(True)
            headings.addWidget(self.brief_title)
            self.brief_subtitle = QLabel()
            self.brief_subtitle.setObjectName("heroCopy")
            self.brief_subtitle.setWordWrap(True)
            headings.addWidget(self.brief_subtitle)
            row.addLayout(headings,1)
            self.orb = KnowledgeOrb(self,theme=self.theme,mode=self.mode,
                                    reduce_motion=self.reduce_motion,intensity=self.intensity)
            row.addWidget(self.orb)
            body.addWidget(hero)

            badges = QHBoxLayout()
            self.kind = QLabel()
            self.source = QLabel()
            self.integrity = QLabel()
            for tag in (self.kind, self.source, self.integrity):
                tag.setObjectName("connectionPill")
                tag.setWordWrap(True)
                badges.addWidget(tag)
            body.addLayout(badges)

            official = QFrame()
            official.setObjectName("contentPanel")
            official_layout = QVBoxLayout(official)
            official_layout.setContentsMargins(20, 15, 20, 16)
            official_layout.setSpacing(8)
            self.official_title = QLabel()
            self.official_title.setObjectName("eyebrow")
            official_layout.addWidget(self.official_title)
            self.official_desc = QLabel()
            self.official_desc.setObjectName("pageHint")
            self.official_desc.setWordWrap(True)
            official_layout.addWidget(self.official_desc)
            self.official_five = QLabel()
            self.official_five.setObjectName("pageHint")
            self.official_five.setWordWrap(True)
            official_layout.addWidget(self.official_five)
            official_buttons = QHBoxLayout()
            self.official_buttons = {}
            for name, url in (
                ("hazards", "https://www.nasa.gov/hrp/hazards/"),
                ("risks", "https://www.nasa.gov/hrp/risks/"),
                ("research", "https://www.nasa.gov/hrp/ongoing-hrp-research/"),
            ):
                button = QPushButton()
                button.setObjectName("navButton")
                button.clicked.connect(lambda checked=False, link=url:
                                       QDesktopServices.openUrl(QUrl(link)))
                self.official_buttons[name] = button
                official_buttons.addWidget(button)
            official_layout.addLayout(official_buttons)
            self.official_explain = QLabel()
            self.official_explain.setObjectName("pageHint")
            self.official_explain.setWordWrap(True)
            official_layout.addWidget(self.official_explain)
            body.addWidget(official)

            section = QFrame()
            section.setObjectName("surface")
            group_layout = QVBoxLayout(section)
            group_layout.setContentsMargins(22, 20, 22, 19)
            self.section_title = QLabel()
            self.section_title.setObjectName("eyebrow")
            group_layout.addWidget(self.section_title)
            self.section_notes = []
            for _ in range(4):
                label = QLabel()
                label.setObjectName("pageHint")
                label.setWordWrap(True)
                group_layout.addWidget(label)
                self.section_notes.append(label)
            self.count_label = QLabel()
            self.count_label.setObjectName("eyebrow")
            group_layout.addWidget(self.count_label)
            body.addWidget(section)

            warning = QFrame()
            warning.setObjectName("contentPanel")
            caution_layout = QVBoxLayout(warning)
            caution_layout.setContentsMargins(20, 17, 20, 17)
            self.warning = QLabel()
            self.warning.setWordWrap(True)
            self.warning.setObjectName("pageHint")
            self.challenge_note = QLabel()
            self.challenge_note.setWordWrap(True)
            self.challenge_note.setObjectName("pageHint")
            caution_layout.addWidget(self.warning)
            caution_layout.addWidget(self.challenge_note)
            body.addWidget(warning)

            actions = QHBoxLayout()
            self.start = QPushButton()
            self.start.setObjectName("primaryAction")
            self.start.clicked.connect(self.begin)
            actions.addWidget(self.start)
            self.source_button = QPushButton()
            self.source_button.clicked.connect(self.open_source)
            actions.addWidget(self.source_button)
            self.back_button = QPushButton()
            self.back_button.clicked.connect(self.home_requested.emit)
            actions.addWidget(self.back_button)
            actions.addStretch(1)
            body.addLayout(actions)
            # Genuine NASA OSDR challenge-relevant sources are offered separately.
            # Their numerical data are NOT misattributed to this 1962 archive.
            research = QHBoxLayout()
            self.osdr569 = QPushButton()
            self.osdr569.clicked.connect(lambda: self.open_osdr("569"))
            research.addWidget(self.osdr569)
            self.osdr575 = QPushButton()
            self.osdr575.clicked.connect(lambda: self.open_osdr("575"))
            research.addWidget(self.osdr575)
            research.addStretch(1)
            body.addLayout(research)
            self.osdr_notice = QLabel()
            self.osdr_notice.setObjectName("pageHint")
            self.osdr_notice.setWordWrap(True)
            body.addWidget(self.osdr_notice)
            body.addStretch(1)
            self.pages.addWidget(self.briefing)

        def _build_replay(self):
            self.replay, body = self._scroll_page()
            self.play_kicker = QLabel()
            self.play_kicker.setObjectName("eyebrow")
            body.addWidget(self.play_kicker)
            titlebar = QHBoxLayout()
            self.play_title = QLabel()
            self.play_title.setObjectName("heroTitle")
            titlebar.addWidget(self.play_title,1)
            self.not_live = QLabel()
            self.not_live.setObjectName("connectionPill")
            titlebar.addWidget(self.not_live)
            body.addLayout(titlebar)
            self.play_lead = QLabel()
            self.play_lead.setObjectName("heroCopy")
            self.play_lead.setWordWrap(True)
            body.addWidget(self.play_lead)

            group_buttons = QHBoxLayout()
            self.group_buttons = []
            for ix in range(4):
                btn = QPushButton()
                btn.setCheckable(True)
                btn.setAccessibleName(f"NASA data group {ix+1}")
                btn.clicked.connect(lambda checked=False, i=ix: self.select_group(i))
                group_buttons.addWidget(btn)
                self.group_buttons.append(btn)
            body.addLayout(group_buttons)

            control = QHBoxLayout()
            self.stage_label = QLabel()
            self.stage_label.setObjectName("eyebrow")
            control.addWidget(self.stage_label)
            control.addStretch()
            self.back_stage_button = QPushButton()
            self.back_stage_button.clicked.connect(self.prev_stage)
            control.addWidget(self.back_stage_button)
            self.next_stage_button = QPushButton()
            self.next_stage_button.clicked.connect(self.next_stage)
            control.addWidget(self.next_stage_button)
            self.autoplay = QPushButton()
            self.autoplay.setCheckable(True)
            self.autoplay.clicked.connect(self.toggle_autoplay)
            control.addWidget(self.autoplay)
            body.addLayout(control)

            stages = QHBoxLayout()
            self.stage_list = QListWidget()
            self.stage_list.setMaximumWidth(255)
            self.stage_list.setMinimumWidth(160)
            self.stage_list.currentRowChanged.connect(self.select_stage)
            stages.addWidget(self.stage_list, 1)
            chart_panel = QFrame()
            chart_panel.setObjectName("contentPanel")
            chart_content = QVBoxLayout(chart_panel)
            chart_content.setContentsMargins(17, 12, 17, 13)
            self.period_title = QLabel()
            self.period_title.setObjectName("heading")
            self.period_title.setWordWrap(True)
            chart_content.addWidget(self.period_title)
            self.graph = HistoricalBars()
            self.graph.chosen.connect(self.stage_list.setCurrentRow)
            chart_content.addWidget(self.graph)
            self.chart_note = QLabel()
            self.chart_note.setObjectName("pageHint")
            self.chart_note.setWordWrap(True)
            chart_content.addWidget(self.chart_note)
            stages.addWidget(chart_panel, 3)
            body.addLayout(stages)

            self.metrics_heading = QLabel()
            self.metrics_heading.setObjectName("eyebrow")
            body.addWidget(self.metrics_heading)
            cards = QGridLayout()
            cards.setHorizontalSpacing(13)
            cards.setVerticalSpacing(13)
            self.kpi = []
            for i in range(4):
                panel = QFrame()
                panel.setObjectName("surface")
                layout = QVBoxLayout(panel)
                layout.setContentsMargins(18,15,18,15)
                label = QLabel()
                label.setObjectName("eyebrow")
                label.setWordWrap(True)
                layout.addWidget(label)
                value = QLabel("—")
                value.setObjectName("heading")
                value.setWordWrap(True)
                layout.addWidget(value)
                details = QLabel()
                details.setObjectName("pageHint")
                details.setWordWrap(True)
                layout.addWidget(details)
                cards.addWidget(panel,i//2,i%2)
                self.kpi.append((label,value,details))
            body.addLayout(cards)

            table_frame = QFrame()
            table_frame.setObjectName("contentPanel")
            tablay = QVBoxLayout(table_frame)
            tablay.setContentsMargins(16,14,16,16)
            self.table_label = QLabel()
            self.table_label.setObjectName("eyebrow")
            tablay.addWidget(self.table_label)
            self.table = QTableWidget(0,4)
            self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.table.setAlternatingRowColors(True)
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.verticalHeader().setVisible(False)
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.setMinimumHeight(240)
            tablay.addWidget(self.table)
            body.addWidget(table_frame)

            self.caveat = QLabel()
            self.caveat.setObjectName("pageHint")
            self.caveat.setWordWrap(True)
            body.addWidget(self.caveat)
            self.safety = QLabel()
            self.safety.setObjectName("pageHint")
            self.safety.setWordWrap(True)
            body.addWidget(self.safety)
            footer = QHBoxLayout()
            self.brief_button = QPushButton()
            self.brief_button.clicked.connect(self.show_briefing)
            footer.addWidget(self.brief_button)
            self.source_again = QPushButton()
            self.source_again.clicked.connect(self.open_source)
            footer.addWidget(self.source_again)
            footer.addStretch()
            body.addLayout(footer)
            self.pages.addWidget(self.replay)

        def begin(self):
            try:
                self.doc = load_real_nasa_data()
            except (OSError, ValueError, TypeError, KeyError) as error:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(self, self.t("intro.source"),
                    self.t("replay.error", error=type(error).__name__))
                return
            self.select_group(0)
            self.pages.setCurrentWidget(self.replay)

        def select_group(self, index):
            if not self.doc or not 0 <= index < len(self.doc["groups"]):
                return
            self._stop_autoplay()
            self.group_index = index
            self.group = self.doc["groups"][index]
            self.stage_list.blockSignals(True)
            self.stage_list.clear()
            for record in self.group["records"]:
                self.stage_list.addItem(record["title"][self.language])
            self.stage_list.blockSignals(False)
            for i, button in enumerate(self.group_buttons):
                button.setChecked(i == index)
            self.stage_list.setCurrentRow(0)
            self.select_stage(0)

        def select_stage(self, index):
            if not self.group or not 0 <= index < len(self.group["records"]):
                return
            self.record = self.group["records"][index]
            self.period_title.setText(self.record["title"][self.language])
            self.chart_note.setText(self.group["note"][self.language])
            self.caveat.setText(self.t("replay.caveat",
                                    note=self.group["note"][self.language]))
            metrics = self.record["measures"]
            names = self.doc["metric_names"]
            ids = list(metrics)
            for i,(label,value,details) in enumerate(self.kpi):
                if i >= len(ids):
                    label.setText("—");value.setText("—");details.setText("")
                    continue
                key=ids[i]; obs=metrics[key]
                label.setText(names[key][self.language])
                value.setText(self._reading(obs))
                details.setText(self._descriptor(obs))
            # Only actual numeric values plotted; ranges/missing values are never interpolated.
            plot_id = next((k for k in ids if any(x is not None for x in
                           measured_points(self.group["records"],k))), None)
            self.graph.set_series(measured_points(self.group["records"],plot_id)
                                  if plot_id else (),self.theme,self.mode)
            self.table.setRowCount(len(ids))
            for r,key in enumerate(ids):
                measure=metrics[key]
                row=[names[key][self.language],self._reading(measure),
                     self._descriptor(measure),str(self.group["table"])]
                for col,text in enumerate(row):
                    cell=QTableWidgetItem(text)
                    cell.setToolTip(text)
                    self.table.setItem(r,col,cell)

        def _reading(self,measure):
            value=measure.get("value")
            return self.t("replay.missing") if value is None else f"{value} {measure['unit']}"

        def _descriptor(self,measure):
            if measure.get("value") is None:
                return self.t("replay.unavailable")
            pieces=[]
            if measure.get("qualifier")=="phase_mean":
                pieces.append(self.t("replay.mean"))
            elif measure.get("qualifier")=="instrument_category_I_caveated":
                pieces.append(self.t("replay.inflight"))
            elif measure.get("qualifier")=="reported_range":
                pieces.append(self.t("replay.range"))
            else:
                pieces.append(self.t("replay.reported"))
            if measure.get("range"):
                pieces.append(self.t("replay.range")+": "+str(measure["range"]))
            if measure.get("sample_count") is not None:
                pieces.append(self.t("replay.count")+": "+str(measure["sample_count"]))
            return " · ".join(pieces)

        def prev_stage(self):
            if self.group:
                i=max(0,self.stage_list.currentRow()-1)
                self.stage_list.setCurrentRow(i)

        def next_stage(self):
            if self.group:
                n=len(self.group["records"])
                self.stage_list.setCurrentRow((self.stage_list.currentRow()+1)%n)

        def toggle_autoplay(self, checked):
            if checked and self.doc and not self.reduce_motion:
                self.timer.start()
            else:
                self._stop_autoplay()
            self.autoplay.setText(self.t("replay.pause" if self.timer.isActive()
                                      else "replay.play"))

        def _stop_autoplay(self):
            if hasattr(self,"timer"):
                self.timer.stop()
            self.autoplay.blockSignals(True)
            self.autoplay.setChecked(False)
            self.autoplay.blockSignals(False)
            self.autoplay.setText(self.t("replay.play"))

        def show_briefing(self):
            self._stop_autoplay()
            self.pages.setCurrentWidget(self.briefing)

        def open_source(self):
            QDesktopServices.openUrl(QUrl(
                "https://www.nasa.gov/wp-content/uploads/2026/01/ma07-te2.pdf"))

        def open_osdr(self, study_id: str):
            if study_id not in ("569", "575"):
                return
            QDesktopServices.openUrl(QUrl(
                "https://osdr.nasa.gov/bio/repo/data/studies/OSD-" + study_id))

        def set_locale(self, locale):
            self.language = normalize_locale(locale)
            self.brief_kicker.setText(self.t("hero.kicker"))
            self.brief_title.setText(self.t("hero.title"))
            self.brief_subtitle.setText(self.t("hero.subtitle"))
            self.kind.setText(self.t("intro.kind")+"\n"+self.t("intro.integrityValue"))
            self.source.setText(self.t("intro.source")+"\n"+self.t("intro.sourceValue"))
            self.integrity.setText(self.t("intro.integrity")+"\n"+self.t("intro.integrityValue"))
            self.section_title.setText(self.t("intro.sections"))
            for label,key in zip(self.section_notes,
                    ("intro.flight","intro.clinical","intro.blood","intro.pressure")):
                label.setText("◈  "+self.t(key))
            self.count_label.setText(self.t("intro.count"))
            self.warning.setText(self.t("intro.warning"))
            self.challenge_note.setText(self.t("intro.notchallenge"))
            self.official_title.setText(self.t("official.title"))
            self.official_desc.setText(self.t("official.description"))
            self.official_five.setText(self.t("official.five"))
            self.official_explain.setText(self.t("official.explain"))
            for name, button in self.official_buttons.items():
                button.setText(self.t("official." + name))
            self.start.setText(self.t("intro.start"))
            self.source_button.setText(self.t("intro.visit"))
            self.osdr569.setText(self.t("intro.osdr569"))
            self.osdr575.setText(self.t("intro.osdr575"))
            self.osdr_notice.setText(self.t("intro.osdrWarning"))
            self.back_button.setText(self.t("intro.return"))
            self.play_kicker.setText(self.t("replay.kicker"))
            self.play_title.setText(self.t("replay.title"))
            self.not_live.setText(self.t("replay.notLive"))
            self.play_lead.setText(self.t("replay.lead"))
            self.stage_label.setText(self.t("replay.phase"))
            self.back_stage_button.setText(self.t("replay.previous"))
            self.next_stage_button.setText(self.t("replay.next"))
            self.autoplay.setText(self.t("replay.pause" if self.timer.isActive()
                                       else "replay.play"))
            self.metrics_heading.setText(self.t("replay.metrics"))
            self.table_label.setText(self.t("replay.table"))
            self.table.setHorizontalHeaderLabels([self.t("replay.col."+x)
                            for x in ("metric","value","details","source")])
            self.safety.setText(self.t("replay.notice"))
            self.brief_button.setText(self.t("replay.briefing"))
            self.source_again.setText(self.t("replay.open"))
            if self.doc:
                for i,button in enumerate(self.group_buttons):
                    button.setText(self.doc["groups"][i]["title"][self.language])
                if self.group:
                    index=max(0,self.stage_list.currentRow())
                    self.stage_list.blockSignals(True)
                    self.stage_list.clear()
                    for record in self.group["records"]:
                        self.stage_list.addItem(record["title"][self.language])
                    self.stage_list.blockSignals(False)
                    self.stage_list.setCurrentRow(index)
                    self.select_stage(index)
            else:
                for i,button in enumerate(self.group_buttons):
                    button.setText(self.t(("intro.flight","intro.clinical",
                                          "intro.blood","intro.pressure")[i]))

        def set_visuals(self, theme, mode, reduce_motion=False, intensity=48):
            self.theme=theme
            self.mode=mode
            self.reduce_motion=bool(reduce_motion)
            self.intensity=max(0,min(100,int(intensity)))
            self.orb.set_visuals(theme,mode,self.reduce_motion,self.intensity)
            if self.reduce_motion:
                self._stop_autoplay()
            if self.group:
                self.select_stage(max(0,self.stage_list.currentRow()))

        def hideEvent(self,event):
            self._stop_autoplay()
            super().hideEvent(event)

    return NasaHackathonDemo()
