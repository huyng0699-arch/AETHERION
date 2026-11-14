"""Native, clearly marked synthetic-patient explorer for usability testing.

The historical NASA replay and production health store are never modified by
this screen. Every view reads the same separate locally seeded demo SQLite DB.
"""
from __future__ import annotations

from datetime import date
from math import isfinite

from .synthetic_patients import (
    DAYS, DATASET_ID, METRICS, SOURCE_ID, build_demo_database,
    day_values, demo_stats, latest, series, subjects,
)


def build_synthetic_patient_demo(parent=None, *, locale="en",
                                 theme="daybreak", mode="light"):
    """Return an offline PySide6 patient-test workspace (Qt imports are lazy)."""
    from PySide6.QtCore import Qt, Signal, QDate, QTimer, QPointF, QRectF
    from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath
    from PySide6.QtWidgets import (
        QAbstractItemView, QComboBox, QDateEdit, QFrame, QGridLayout,
        QHBoxLayout, QHeaderView, QLabel, QPushButton, QScrollArea,
        QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
        QMessageBox,
    )
    from ...localization import normalize_locale, tr
    from ...visual_theme import palette_for

    class TrendChart(QWidget):
        def __init__(self):
            super().__init__()
            self.points = []
            self.theme, self.mode = theme, mode
            self.setMinimumHeight(260)
            self.setObjectName("demoSyntheticChart")

        def set_data(self, data, theme_name, display_mode):
            self.points = [
                (item["day_utc"], item["value"]) for item in data
                if isinstance(item.get("value"), (int, float))
                and isfinite(item["value"])
            ]
            self.theme, self.mode = theme_name, display_mode
            self.update()

        def paintEvent(self, event):
            super().paintEvent(event)
            pal = palette_for(self.theme, self.mode)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            chart = self.rect().adjusted(48, 23, -22, -40)
            if chart.width() < 45 or chart.height() < 45:
                painter.end()
                return
            axis = QColor(pal.muted)
            axis.setAlpha(115)
            painter.setPen(QPen(axis, 1))
            for i in range(5):
                y = chart.top() + chart.height() * i / 4
                painter.drawLine(chart.left(), int(y), chart.right(), int(y))
            if not self.points:
                painter.end()
                return
            values = [value for _, value in self.points]
            lo, hi = min(values), max(values)
            padding = max((hi - lo) * .12, max(abs(lo), 1) * .01)
            lo -= padding
            hi += padding
            span = max(hi - lo, 1e-9)
            n = len(self.points)
            curve = QPainterPath()
            for ix, (_, value) in enumerate(self.points):
                x = chart.left() + chart.width() * ix / max(n-1, 1)
                y = chart.bottom() - chart.height() * (value-lo)/span
                if ix == 0:
                    curve.moveTo(x, y)
                else:
                    curve.lineTo(x, y)
            painter.setPen(QPen(QColor(pal.accent), 2.5))
            painter.drawPath(curve)
            painter.setPen(QPen(QColor(pal.text), 1))
            painter.drawText(2, chart.top()+7, f"{hi:.1f}")
            painter.drawText(2, chart.bottom(), f"{lo:.1f}")
            painter.drawText(chart.left(), chart.bottom()+22, self.points[0][0])
            painter.drawText(
                QRectF(chart.left(), chart.bottom()+7, chart.width(),
                       22), Qt.AlignmentFlag.AlignRight, self.points[-1][0]
            )
            last_x = chart.right()
            last_y = chart.bottom() - chart.height() * (values[-1]-lo)/span
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(pal.accent))
            painter.drawEllipse(QPointF(last_x, last_y), 5, 5)
            painter.end()

    class PatientDemo(QWidget):
        back_requested = Signal()

        def __init__(self):
            super().__init__(parent)
            self.language = normalize_locale(locale)
            self.theme, self.mode = theme, mode
            self.ready = False
            self._stats = None
            self._first_day = None
            self._last_day = None
            self.setObjectName("syntheticPatientDemo")
            outer = QVBoxLayout(self)
            outer.setContentsMargins(26, 18, 26, 20)
            outer.setSpacing(13)

            header = QHBoxLayout()
            self.title = QLabel()
            self.title.setObjectName("heroTitle")
            header.addWidget(self.title, 1)
            self.back = QPushButton()
            self.back.setObjectName("navButton")
            self.back.clicked.connect(self.back_requested.emit)
            header.addWidget(self.back)
            outer.addLayout(header)

            self.state = QLabel()
            self.state.setObjectName("connectionPill")
            self.state.setWordWrap(True)
            outer.addWidget(self.state)
            self.summary = QLabel()
            self.summary.setObjectName("heroCopy")
            self.summary.setWordWrap(True)
            outer.addWidget(self.summary)

            self.tabs = QTabWidget()
            self.tabs.setDocumentMode(True)
            outer.addWidget(self.tabs, 1)
            self._build_crew()
            self._build_personal()
            self._build_monitor()
            self._build_history()
            self._build_provenance()
            self.set_locale(self.language)

        def t(self, key, **values):
            return tr(self.language, "demo.synthetic." + key, **values)

        def _page(self):
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(17, 18, 17, 20)
            layout.setSpacing(14)
            return widget, layout

        def _build_crew(self):
            self.crew, box = self._page()
            self.crew_help = QLabel()
            self.crew_help.setObjectName("pageHint")
            self.crew_help.setWordWrap(True)
            box.addWidget(self.crew_help)
            self.crew_table = QTableWidget(0, 6)
            self._configure_table(self.crew_table, height=240)
            self.crew_table.cellDoubleClicked.connect(self._open_crew_row)
            box.addWidget(self.crew_table)
            self.crew_note = QLabel()
            self.crew_note.setObjectName("pageHint")
            self.crew_note.setWordWrap(True)
            box.addWidget(self.crew_note)
            box.addStretch()
            self.tabs.addTab(self.crew, "")

        def _build_personal(self):
            self.personal, box = self._page()
            row = QHBoxLayout()
            self.subject_label = QLabel()
            row.addWidget(self.subject_label)
            self.subject_combo = QComboBox()
            self.subject_combo.setMinimumWidth(210)
            self.subject_combo.currentIndexChanged.connect(self.refresh_all)
            row.addWidget(self.subject_combo, 1)
            self.day_label = QLabel()
            row.addWidget(self.day_label)
            self.day_picker = QDateEdit()
            self.day_picker.setCalendarPopup(True)
            self.day_picker.setDisplayFormat("yyyy-MM-dd")
            self.day_picker.dateChanged.connect(self.refresh_day)
            row.addWidget(self.day_picker)
            box.addLayout(row)

            self.personal_note = QLabel()
            self.personal_note.setObjectName("pageHint")
            self.personal_note.setWordWrap(True)
            box.addWidget(self.personal_note)
            cards = QGridLayout()
            cards.setSpacing(12)
            self.kpis = {}
            for i, (metric, unit) in enumerate(METRICS[:8]):
                panel = QFrame()
                panel.setObjectName("surface")
                detail = QVBoxLayout(panel)
                detail.setContentsMargins(16, 13, 16, 13)
                name = QLabel()
                name.setObjectName("eyebrow")
                name.setWordWrap(True)
                detail.addWidget(name)
                number = QLabel("—")
                number.setObjectName("heading")
                detail.addWidget(number)
                source = QLabel()
                source.setObjectName("pageHint")
                source.setWordWrap(True)
                detail.addWidget(source)
                cards.addWidget(panel, i // 4, i % 4)
                self.kpis[metric] = (name, number, source)
            box.addLayout(cards)
            self.day_heading = QLabel()
            self.day_heading.setObjectName("eyebrow")
            box.addWidget(self.day_heading)
            self.day_table = QTableWidget(0, 4)
            self._configure_table(self.day_table, height=260)
            box.addWidget(self.day_table)
            self.tabs.addTab(self.personal, "")

        def _build_monitor(self):
            self.monitor, box = self._page()
            selectors = QHBoxLayout()
            self.metric_label = QLabel()
            selectors.addWidget(self.metric_label)
            self.metric_combo = QComboBox()
            for metric, unit in METRICS:
                self.metric_combo.addItem(metric, metric)
            self.metric_combo.currentIndexChanged.connect(self.refresh_metric)
            selectors.addWidget(self.metric_combo, 2)
            self.period_label = QLabel()
            selectors.addWidget(self.period_label)
            self.period = QComboBox()
            for days in (30, 90, 180, 365, DAYS):
                self.period.addItem(str(days), days)
            self.period.setCurrentIndex(2)
            self.period.currentIndexChanged.connect(self.refresh_metric)
            selectors.addWidget(self.period, 1)
            box.addLayout(selectors)
            self.trend = TrendChart()
            box.addWidget(self.trend, 1)
            self.trend_note = QLabel()
            self.trend_note.setObjectName("pageHint")
            self.trend_note.setWordWrap(True)
            box.addWidget(self.trend_note)
            self.trend_summary = QLabel()
            self.trend_summary.setObjectName("heading")
            box.addWidget(self.trend_summary)
            self.tabs.addTab(self.monitor, "")

        def _build_history(self):
            self.history, box = self._page()
            self.history_note = QLabel()
            self.history_note.setObjectName("pageHint")
            self.history_note.setWordWrap(True)
            box.addWidget(self.history_note)
            self.history_table = QTableWidget(0, 5)
            self._configure_table(self.history_table, height=330)
            box.addWidget(self.history_table)
            self.tabs.addTab(self.history, "")

        def _build_provenance(self):
            self.provenance, box = self._page()
            self.source_heading = QLabel()
            self.source_heading.setObjectName("heading")
            box.addWidget(self.source_heading)
            self.source_info = QLabel()
            self.source_info.setObjectName("pageHint")
            self.source_info.setWordWrap(True)
            self.source_info.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            box.addWidget(self.source_info)
            self.regenerate = QPushButton()
            self.regenerate.setObjectName("navButton")
            self.regenerate.clicked.connect(self._regenerate)
            box.addWidget(self.regenerate)
            box.addStretch()
            self.tabs.addTab(self.provenance, "")

        @staticmethod
        def _configure_table(table, height=250):
            table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            table.setAlternatingRowColors(True)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setSectionResizeMode(
                QHeaderView.ResizeMode.Stretch
            )
            table.setMinimumHeight(height)

        @staticmethod
        def _text_item(value):
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            return item

        def start(self):
            """Called only after the full Demo briefing CTA is selected."""
            self.state.setText(self.t("loading"))
            self.tabs.setEnabled(False)
            QTimer.singleShot(0, self._load)

        def _load(self, reset=False):
            try:
                stats = build_demo_database(reset=reset)
                roster = subjects()
                if not stats["is_synthetic"] or len(roster) != 5:
                    raise ValueError("Invalid synthetic dataset")
            except (OSError, ValueError, RuntimeError) as error:
                self.ready = False
                self.state.setText(self.t("error", code=type(error).__name__))
                self.tabs.setEnabled(False)
                return
            self._stats = stats
            self._first_day, self._last_day = stats["from"], stats["to"]
            self.subject_combo.blockSignals(True)
            old_id = self.subject_combo.currentData()
            self.subject_combo.clear()
            for row in roster:
                self.subject_combo.addItem(
                    f"{row['display_name']}  /  {row['subject_id']}",
                    row["subject_id"]
                )
            if old_id:
                previous = self.subject_combo.findData(old_id)
                if previous >= 0:
                    self.subject_combo.setCurrentIndex(previous)
            self.subject_combo.blockSignals(False)
            self.day_picker.blockSignals(True)
            first = QDate.fromString(self._first_day, "yyyy-MM-dd")
            last = QDate.fromString(self._last_day, "yyyy-MM-dd")
            self.day_picker.setDateRange(first, last)
            self.day_picker.setDate(last)
            self.day_picker.blockSignals(False)
            self.ready = True
            self.tabs.setEnabled(True)
            self.set_locale(self.language)
            self._render_crew()
            self.refresh_all()
            self.tabs.setCurrentWidget(self.crew)

        def set_locale(self, language):
            self.language = normalize_locale(language)
            self.title.setText(self.t("title"))
            self.back.setText(self.t("guide"))
            self.state.setText(self.t("state") if self.ready else self.t("standby"))
            self.summary.setText(
                self.t("count", patients=self._stats["subjects"],
                       days=self._stats["days"], metrics=self._stats["metrics"],
                       points=self._stats["observations"])
                if self._stats else self.t("standby")
            )
            for i, key in enumerate(("crew", "personal", "monitor", "history", "source")):
                self.tabs.setTabText(i, self.t("tab." + key))
            self.crew_help.setText(self.t("crew.help"))
            self.crew_note.setText(self.t("crew.note"))
            self.crew_table.setHorizontalHeaderLabels(
                [self.t("col." + k) for k in
                 ("patient", "age", "heart_rate", "spo2", "latest", "status")]
            )
            self.subject_label.setText(self.t("patient"))
            self.day_label.setText(self.t("date"))
            self.personal_note.setText(self.t("personal.note"))
            self.day_heading.setText(self.t("day.title"))
            self.day_table.setHorizontalHeaderLabels(
                [self.t("col." + k) for k in
                 ("metric", "value", "time", "source")]
            )
            self.metric_label.setText(self.t("metric"))
            self.period_label.setText(self.t("period"))
            for index, (metric, _) in enumerate(METRICS):
                self.metric_combo.setItemText(index, self.t("metric." + metric))
            for index, days in enumerate((30, 90, 180, 365, DAYS)):
                self.period.setItemText(index, self.t("days", count=days))
            self.trend_note.setText(self.t("monitor.note"))
            self.history_note.setText(self.t("history.note"))
            self.history_table.setHorizontalHeaderLabels(
                [self.t("col." + k) for k in
                 ("date", "metric", "value", "unit", "source")]
            )
            self.source_heading.setText(self.t("source.title"))
            self.regenerate.setText(self.t("reset"))
            self.source_info.setText(
                self.t("source.details", dataset=DATASET_ID, source=SOURCE_ID,
                       from_date=self._first_day or "—",
                       to_date=self._last_day or "—")
            )
            for metric, (label, _, note) in self.kpis.items():
                label.setText(self.t("metric." + metric))
                note.setText(self.t("kpi.source"))
            if self.ready:
                self._render_crew()
                self.refresh_all()

        def set_visuals(self, theme_name, display_mode):
            self.theme, self.mode = theme_name, display_mode
            if self.ready:
                self.refresh_metric()

        def _open_crew_row(self, row, column):
            if not self.ready or not 0 <= row < self.subject_combo.count():
                return
            self.subject_combo.setCurrentIndex(row)
            self.tabs.setCurrentWidget(self.personal)

        def _render_crew(self):
            if not self.ready:
                return
            roster = subjects()
            self.crew_table.setRowCount(len(roster))
            for row, person in enumerate(roster):
                reading = {m["metric"]: m for m in latest(person["subject_id"])}
                hr, oxy = reading.get("heart_rate"), reading.get("spo2")
                values = (
                    person["display_name"] + " · " + person["subject_id"],
                    person["age"],
                    f"{hr['value']:g} bpm" if hr else "—",
                    f"{oxy['value']:g} %" if oxy else "—",
                    self._last_day, self.t("state.short"),
                )
                for col, value in enumerate(values):
                    self.crew_table.setItem(row, col, self._text_item(value))

        def refresh_all(self, *_):
            if not self.ready or not self.subject_combo.currentData():
                return
            self.refresh_day()
            self.refresh_metric()

        def refresh_day(self, *_):
            if not self.ready:
                return
            subject = self.subject_combo.currentData()
            chosen = self.day_picker.date().toString("yyyy-MM-dd")
            rows = day_values(subject, chosen)
            by_metric = {row["metric"]: row for row in rows}
            for metric, (_, value, _) in self.kpis.items():
                row = by_metric.get(metric)
                value.setText(
                    f"{row['value']:g} {row['unit']}" if row else self.t("missing")
                )
            self.day_table.setRowCount(len(rows))
            for i, item in enumerate(rows):
                values = (
                    self.t("metric." + item["metric"]),
                    f"{item['value']:g} {item['unit']}",
                    item["observed_at"],
                    item["source_id"],
                )
                for col, value in enumerate(values):
                    self.day_table.setItem(i, col, self._text_item(value))

        def refresh_metric(self, *_):
            if not self.ready or not self.subject_combo.currentData():
                return
            metric = self.metric_combo.currentData()
            window = self.period.currentData() or DAYS
            rows = series(self.subject_combo.currentData(), metric, limit=window)
            self.trend.set_data(rows, self.theme, self.mode)
            self.trend_summary.setText(
                self.t("monitor.summary", n=len(rows), days=window,
                       name=self.t("metric." + metric))
            )
            self.history_table.setRowCount(len(rows))
            for i, row in enumerate(reversed(rows)):
                values = (row["day_utc"], self.t("metric." + metric),
                          f"{row['value']:g}", row["unit"], row["source_id"])
                for col, value in enumerate(values):
                    self.history_table.setItem(i, col, self._text_item(value))

        def _regenerate(self):
            response = QMessageBox.question(
                self, self.t("reset"), self.t("reset.confirm"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if response == QMessageBox.StandardButton.Yes:
                self.ready = False
                self.state.setText(self.t("loading"))
                self.tabs.setEnabled(False)
                QTimer.singleShot(0, lambda: self._load(reset=True))

    return PatientDemo()
