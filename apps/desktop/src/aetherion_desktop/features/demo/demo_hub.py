"""Native landing dashboard for every source successfully loaded into demo memory."""
from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from ...localization import normalize_locale, tr


class DemoDataHub(QWidget):
    replay_requested = Signal()
    library_requested = Signal(str)
    briefing_requested = Signal()

    def __init__(self, parent=None, *, locale="vi"):
        super().__init__(parent)
        self.language = normalize_locale(locale)
        self.bundle = None
        root = QVBoxLayout(self)
        root.setContentsMargins(0,0,0,0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        root.addWidget(area)
        contents = QWidget()
        area.setWidget(contents)
        column = QVBoxLayout(contents)
        column.setContentsMargins(32,23,32,28)
        column.setSpacing(16)
        self.eyebrow = QLabel()
        self.eyebrow.setObjectName("eyebrow")
        column.addWidget(self.eyebrow)
        self.title = QLabel()
        self.title.setObjectName("heroTitle")
        column.addWidget(self.title)
        self.lead = QLabel()
        self.lead.setObjectName("heroCopy")
        self.lead.setWordWrap(True)
        column.addWidget(self.lead)

        self.cards = {}
        for key in ("archive","cliff","hazards","symptoms"):
            panel = QFrame()
            panel.setObjectName("contentPanel")
            row = QHBoxLayout(panel)
            row.setContentsMargins(22,14,22,14)
            info = QVBoxLayout()
            info.setSpacing(5)
            heading = QLabel()
            heading.setObjectName("eyebrow")
            info.addWidget(heading)
            counter = QLabel()
            counter.setObjectName("heading")
            counter.setWordWrap(True)
            info.addWidget(counter)
            description = QLabel()
            description.setObjectName("pageHint")
            description.setWordWrap(True)
            info.addWidget(description)
            row.addLayout(info,1)
            action = QPushButton()
            action.setObjectName("primaryAction" if key=="archive" else "navButton")
            if key=="archive":
                action.clicked.connect(self.replay_requested.emit)
            else:
                action.clicked.connect(lambda checked=False, item=key:
                                       self.library_requested.emit(
                                         "hazards" if item=="hazards" else
                                         "symptoms" if item=="symptoms" else "cliff"))
            row.addWidget(action)
            self.cards[key] = (heading,counter,description,action)
            column.addWidget(panel)
        self.summary = QLabel()
        self.summary.setObjectName("pageHint")
        self.summary.setWordWrap(True)
        column.addWidget(self.summary)
        self.limitations = QLabel()
        self.limitations.setObjectName("pageHint")
        self.limitations.setWordWrap(True)
        column.addWidget(self.limitations)
        footer = QHBoxLayout()
        self.sources = QPushButton()
        self.sources.setObjectName("navButton")
        self.sources.clicked.connect(self.briefing_requested.emit)
        footer.addWidget(self.sources)
        footer.addStretch()
        column.addLayout(footer)
        self.set_locale(locale)

    def t(self,key,**kwargs):
        return tr(self.language,"demo.hub."+key,**kwargs)

    def set_bundle(self,bundle):
        self.bundle = bundle
        self._refresh()

    def set_locale(self,language):
        self.language = normalize_locale(language)
        self.eyebrow.setText(self.t("kicker"))
        self.title.setText(self.t("title"))
        self.lead.setText(self.t("lead"))
        self.sources.setText(self.t("intro"))
        self._refresh()

    def _refresh(self):
        counts = (self.bundle or {}).get("counts", {})
        n={
            "archive": self.t("archiveCount",timepoints=counts.get("ma7_timepoints",0),
                             values=counts.get("ma7_non_null_values",0)),
            "cliff": self.t("cliffCount",loaded=counts.get("cliff",0),
                            expected=counts.get("cliff_expected",119)),
            "hazards": self.t("hazardCount",loaded=counts.get("hazards",0),
                              expected=counts.get("hazards_expected",5)),
            "symptoms": self.t("symptomsCount",loaded=counts.get("symptoms",0),
                               expected=counts.get("symptoms_expected",819)),
        }
        for key,(heading,counter,description,button) in self.cards.items():
            heading.setText(self.t(key))
            counter.setText(n[key])
            description.setText(self.t(key+"Desc"))
            button.setText(self.t("enter"))
            if key!="archive":
                button.setEnabled(counts.get("cliff" if key=="cliff" else key,0)>0)
        self.summary.setText(self.t("summary",loaded=(self.bundle or {}).get("total_loaded",0)))
        self.limitations.setText(self.t("limitations",
                  missing=len((self.bundle or {}).get("missing_cliff",()))))
        if self.bundle and self.bundle.get("errors"):
            self.limitations.setText(
                self.limitations.text()+"\n"+
                self.t("errors",count=len(self.bundle["errors"])))
        if self.bundle and not any(counts.get(k,0) for k in ("cliff","hazards","symptoms")):
            self.limitations.setText(self.limitations.text()+"\n"+self.t("noCatalog"))
