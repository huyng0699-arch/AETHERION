"""Source-first explanation before the AETHERION fictional patient walkthrough.

The page does not load or seed any SQLite records; Start is the sole explicit
entry into Q-0484's separately owned simulated patient component.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QVBoxLayout, QWidget,
)


WORDS = {
    "en": {
        "kicker": "MISSION OPERATIONS  /  GUIDED EXPERIENCE",
        "title": "Explore a fictional health mission.",
        "lead": "See the complete AETHERION health workflow with fictional patient profiles, daily measurements and long-term history.",
        "badge": "SIMULATED  ·  TEST DATA ONLY",
        "step1": "01  ·  Fictional crew",
        "detail1": "Five invented patient profiles (DEMO-P001–DEMO-P005); no real identities or access tokens.",
        "step2": "02  ·  540-day timeline",
        "detail2": "Twelve metric families over 540 days, with intentionally absent entries. Values are generated for product evaluation, not obtained from humans or hardware.",
        "step3": "03  ·  Explore every screen",
        "detail3": "Crew, Personal, Monitoring, History and Data source tabs are all available in the isolated native app experience.",
        "truth": "Data integrity",
        "truthBody": "The SIMULATED dataset is generated only after you press Start, and is stored in a dedicated local SQLite file. It is not NASA telemetry, a medical record, a patient diagnosis or a real ECG. The data remains separate from the authenticated AETHERION Server.",
        "realTitle": "Want genuine NASA research instead?",
        "realBody": "Mercury-Atlas 7 is a different, explicitly historical archive containing 83 published observations. Its real NASA source values are never reclassified as fictional.",
        "real": "Open NASA MA-7 archive",
        "start": "Start SIMULATED experience",
        "back": "Back to Mission Operations",
        "progress": "Step 1 of 2  ·  Read this briefing, then start the fictional dataset",
        "ack": "Entering is a deliberate demo-only action. All available historical research remains on the separate NASA path.",
    },
    "vi": {
        "kicker": "MISSION OPERATIONS  /  HƯỚNG DẪN TRẢI NGHIỆM",
        "title": "Khám phá một nhiệm vụ sức khỏe giả lập.",
        "lead": "Trải nghiệm đầy đủ AETHERION bằng hồ sơ nhân vật hư cấu, chỉ số theo ngày và lịch sử dài hạn.",
        "badge": "SIMULATED  ·  DỮ LIỆU GIẢ LẬP",
        "step1": "01  ·  Hồ sơ hư cấu",
        "detail1": "Năm hồ sơ giả lập (DEMO-P001–DEMO-P005), không chứa danh tính hay quyền truy cập thật.",
        "step2": "02  ·  Dòng thời gian 540 ngày",
        "detail2": "Mười hai nhóm chỉ số trong 540 ngày và có một số điểm cố ý bỏ trống. Giá trị dành cho đánh giá sản phẩm, không lấy từ con người hay thiết bị.",
        "step3": "03  ·  Khám phá mọi màn hình",
        "detail3": "Truy cập đủ năm thẻ Phi hành đoàn, Cá nhân, Theo dõi, Lịch sử và Nguồn dữ liệu trong ứng dụng native.",
        "truth": "Tính toàn vẹn dữ liệu",
        "truthBody": "Chỉ sau khi bấm Bắt đầu, dữ liệu SIMULATED mới được khởi tạo trong SQLite riêng trên máy. Đây không phải dữ liệu NASA, bệnh án, chẩn đoán hay ECG đo thật. Dữ liệu không nhập vào AETHERION Server đang phục vụ bệnh nhân.",
        "realTitle": "Muốn xem dữ liệu NASA thật?",
        "realBody": "Mercury-Atlas 7 là một bộ hồ sơ lịch sử riêng, chứa 83 giá trị đã công bố. Không đánh dấu những số liệu thật này là giả lập.",
        "real": "Mở kho NASA MA-7",
        "start": "Bắt đầu trải nghiệm SIMULATED",
        "back": "Về Mission Operations",
        "progress": "Bước 1/2  ·  Xem giới thiệu, sau đó mở dữ liệu giả lập",
        "ack": "Đây là thao tác vào chế độ demo chủ động. Tài liệu khoa học NASA vẫn nằm ở đường truy cập riêng.",
    },
}


class SimulatedDemoBriefing(QWidget):
    """Bilingual native consent/briefing page with source-separation contract."""

    start_requested = Signal()
    back_requested = Signal()
    nasa_requested = Signal()

    def __init__(self, parent=None, *, locale="en"):
        super().__init__(parent)
        self.language = "en"
        self.setObjectName("simulatedDemoBriefing")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(area)
        page = QWidget()
        area.setWidget(page)
        root = QVBoxLayout(page)
        root.setContentsMargins(38, 25, 38, 30)
        root.setSpacing(13)

        top = QHBoxLayout()
        self.kicker = QLabel()
        self.kicker.setObjectName("eyebrow")
        top.addWidget(self.kicker, 1)
        self.back = QPushButton()
        self.back.setObjectName("navButton")
        self.back.clicked.connect(self.back_requested.emit)
        top.addWidget(self.back)
        root.addLayout(top)

        self.badge = QLabel()
        self.badge.setObjectName("connectionPill")
        root.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignLeft)
        self.title = QLabel()
        self.title.setObjectName("heroTitle")
        self.title.setWordWrap(True)
        root.addWidget(self.title)
        self.lead = QLabel()
        self.lead.setObjectName("heroCopy")
        self.lead.setWordWrap(True)
        root.addWidget(self.lead)
        self.progress_label = QLabel()
        self.progress_label.setObjectName("eyebrow")
        root.addWidget(self.progress_label)

        steps = QGridLayout()
        steps.setHorizontalSpacing(12)
        steps.setVerticalSpacing(11)
        self.steps = []
        for index in range(3):
            frame = QFrame()
            frame.setObjectName("contentPanel")
            frame_layout = QVBoxLayout(frame)
            frame_layout.setContentsMargins(15, 13, 15, 13)
            head, detail = QLabel(), QLabel()
            head.setObjectName("heading")
            head.setWordWrap(True)
            detail.setObjectName("pageHint")
            detail.setWordWrap(True)
            frame_layout.addWidget(head)
            frame_layout.addWidget(detail, 1)
            steps.addWidget(frame, 0, index)
            self.steps.append((head, detail))
        root.addLayout(steps)

        safety = QFrame()
        safety.setObjectName("contentPanel")
        safety_layout = QVBoxLayout(safety)
        safety_layout.setContentsMargins(20, 12, 20, 13)
        self.truth_title = QLabel()
        self.truth_title.setObjectName("eyebrow")
        self.truth_body = QLabel()
        self.truth_body.setObjectName("pageHint")
        self.truth_body.setWordWrap(True)
        safety_layout.addWidget(self.truth_title)
        safety_layout.addWidget(self.truth_body)
        root.addWidget(safety)

        self.ack = QLabel()
        self.ack.setObjectName("pageHint")
        self.ack.setWordWrap(True)
        root.addWidget(self.ack)
        go = QHBoxLayout()
        self.start = QPushButton()
        self.start.setMinimumHeight(46)
        self.start.setObjectName("primaryAction")
        self.start.clicked.connect(self.start_requested.emit)
        go.addWidget(self.start, 1)
        root.addLayout(go)
        note = QFrame()
        note.setObjectName("contentPanel")
        note_layout = QHBoxLayout(note)
        copy = QVBoxLayout()
        self.real_title = QLabel()
        self.real_title.setObjectName("heading")
        self.real_body = QLabel()
        self.real_body.setObjectName("pageHint")
        self.real_body.setWordWrap(True)
        copy.addWidget(self.real_title)
        copy.addWidget(self.real_body)
        note_layout.addLayout(copy, 1)
        self.real_action = QPushButton()
        self.real_action.setObjectName("navButton")
        self.real_action.clicked.connect(self.nasa_requested.emit)
        note_layout.addWidget(self.real_action)
        root.addWidget(note)
        root.addStretch()
        self.set_locale(locale)

    def set_locale(self, language):
        self.language = "en" if str(language).lower().startswith("en") else "vi"
        d = WORDS[self.language]
        for widget, key in (
            (self.kicker, "kicker"), (self.title, "title"),
            (self.lead, "lead"), (self.badge, "badge"),
            (self.progress_label, "progress"), (self.back, "back"),
            (self.truth_title, "truth"), (self.truth_body, "truthBody"),
            (self.real_title, "realTitle"), (self.real_body, "realBody"),
            (self.real_action, "real"), (self.start, "start"),
            (self.ack, "ack"),
        ):
            widget.setText(d[key])
        for i, (title, body) in enumerate(self.steps, 1):
            title.setText(d[f"step{i}"])
            body.setText(d[f"detail{i}"])
        self.start.setAccessibleName(d["start"])
        self.real_action.setAccessibleName(d["real"])

    def set_visuals(self, theme=None, mode=None, reduce_motion=False, intensity=48):
        """Host's native application palette/styles handle visual modes."""
        return None
