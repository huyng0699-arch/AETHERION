"""Native bilingual metric education for AETHERION desktop."""
from __future__ import annotations
from typing import Callable
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

COPY={
 "en":{"intro":"What the measures tell you","note":"Use the flight medical protocol. This guide explains terms; it does not set mission limits or diagnose.","measure":"What it measures","purpose":"Why it is tracked","tip":"Helpful tip","tip_title":"A quick health tip","tip_body":"A reading is more useful with its time, unit, and context. One number alone cannot tell you what is wrong.","tip_open":"Open guide","tip_close":"Got it","close_name":"Close health tip"},
 "vi":{"intro":"Các phép đo cho biết điều gì","note":"Làm theo quy trình y tế chuyến bay. Cẩm nang giải thích thuật ngữ; không đặt ngưỡng nhiệm vụ và không chẩn đoán.","measure":"Chỉ số đo gì","purpose":"Theo dõi để làm gì","tip":"Mẹo ghi nhận","tip_title":"Mẹo sức khỏe","tip_body":"Số đo hữu ích hơn khi có thời điểm, đơn vị và bối cảnh. Một con số riêng lẻ không cho biết nguyên nhân.","tip_open":"Mở cẩm nang","tip_close":"Đã rõ","close_name":"Đóng mẹo sức khỏe"},
}
# EN/VI title, measure, purpose, tip, and source links.
METRICS=(
("Heart rate / Pulse","Nhịp tim / Mạch","Heartbeats per minute (bpm); it changes with movement, rest, posture, medicines, and other conditions.","Số nhịp tim mỗi phút (bpm); nhịp có thể đổi theo vận động, nghỉ ngơi, tư thế, thuốc và tình trạng cơ thể.","Tracks how the heart responds over time. One pulse value cannot confirm an abnormal rhythm.","Theo dõi tim thay đổi theo thời gian. Một số đo mạch riêng lẻ không xác nhận rối loạn nhịp.","Record time and whether resting or exercising. Compare readings taken in similar conditions.","Ghi thời điểm và bạn đang nghỉ hay vận động. So sánh các lần đo trong điều kiện tương tự.",(("MedlinePlus — Vital signs","https://medlineplus.gov/vitalsigns.html"),("NASA — Arrhythmia evidence","https://humanresearchroadmap.nasa.gov/evidence/other/arrhythmia.pdf"))),
("Blood pressure","Huyết áp","Systolic pressure while the heart beats and diastolic pressure between beats; usually recorded in mmHg.","Huyết áp tâm thu khi tim co bóp và tâm trương giữa các nhịp; thường ghi bằng mmHg.","Describes pressure in the arteries. Posture, activity, food, and medicines can change a reading.","Cho biết áp lực trong động mạch. Tư thế, vận động, thức ăn và thuốc có thể làm kết quả thay đổi.","Use the assigned cuff and method. Record both numbers, unit, time, arm, and posture.","Dùng máy đo và cách đo được hướng dẫn. Ghi đủ hai số, đơn vị, thời điểm, tay và tư thế.",(("MedlinePlus — Measuring blood pressure","https://medlineplus.gov/lab-tests/measuring-blood-pressure/"),)),
("Breathing rate","Tần số thở","Breaths per minute; one inhale-and-exhale cycle is one breath.","Số nhịp thở mỗi phút; một lần hít vào và thở ra là một nhịp.","Rate and pattern help the medical team assess breathing with symptoms and activity.","Tần số và kiểu thở giúp nhân viên y tế đánh giá hô hấp cùng triệu chứng và mức vận động.","Record if measured at rest, after exercise, or during symptoms. Report new breathing difficulty promptly.","Ghi rõ đo lúc nghỉ, sau vận động hay khi có triệu chứng. Báo sớm khi xuất hiện khó thở mới.",(("MedlinePlus — Vital signs","https://medlineplus.gov/vitalsigns.html"),)),
("Body temperature","Nhiệt độ cơ thể","An estimate of body temperature from a particular device and measurement site.","Ước tính nhiệt độ cơ thể bằng thiết bị và vị trí đo cụ thể.","It supports assessment when considered with symptoms and change over time.","Nhiệt độ hỗ trợ đánh giá khi được xem cùng triệu chứng và diễn biến theo thời gian.","Follow the approved thermometer method. Record the device/site and time; methods may not compare directly.","Làm theo cách dùng nhiệt kế đã hướng dẫn. Ghi thiết bị/vị trí và thời điểm; các cách đo có thể không so sánh trực tiếp.",(("MedlinePlus — Vital signs","https://medlineplus.gov/vitalsigns.html"),)),
("Oxygen saturation (SpO₂)","Độ bão hòa oxy (SpO₂)","A pulse oximeter estimates the share of hemoglobin carrying oxygen. It is not a blood-gas test.","Máy đo SpO₂ ước tính tỷ lệ hemoglobin đang mang oxy. Đây không phải xét nghiệm khí máu.","Helps assess oxygenation with breathing and symptoms. Device readings can be inaccurate.","Hỗ trợ đánh giá oxy hóa máu cùng tình trạng thở và triệu chứng. Kết quả thiết bị có thể sai lệch.","Keep still and follow sensor instructions until steady. Cold skin, poor circulation, movement, or nail coverings may affect readings; report symptoms too.","Giữ yên, làm theo hướng dẫn đến khi số đo ổn định. Da lạnh, tuần hoàn kém, cử động hoặc móng phủ có thể ảnh hưởng kết quả; hãy báo triệu chứng.",(("MedlinePlus — Pulse oximetry","https://medlineplus.gov/lab-tests/pulse-oximetry/"),)),
("Electrocardiogram (ECG)","Điện tâm đồ (ECG)","Records electrical signals made by the heart as it beats; the tracing differs from a single pulse number.","Ghi tín hiệu điện do tim tạo ra khi đập; đường ghi khác với một con số nhịp tim.","Clinicians review rate and rhythm from a tracing. It needs clinical interpretation and cannot diagnose by itself.","Nhân viên y tế xem xét tần số và nhịp tim qua đường ghi. ECG cần được diễn giải và không tự chẩn đoán bệnh.","Use assigned device and electrode placement. Record time, activity, and symptoms; do not diagnose from a device label.","Dùng thiết bị và vị trí điện cực được hướng dẫn. Ghi thời điểm, hoạt động và triệu chứng; không tự chẩn đoán từ nhãn thiết bị.",(("MedlinePlus — Electrocardiogram","https://medlineplus.gov/lab-tests/electrocardiogram/"),("NASA — Arrhythmia evidence","https://humanresearchroadmap.nasa.gov/evidence/other/arrhythmia.pdf"))),
("Sleep","Giấc ngủ","Sleep duration and timing, often recorded by diary or device. It is not a vital sign.","Thời lượng và thời điểm ngủ, thường ghi bằng nhật ký hoặc thiết bị. Đây không phải dấu hiệu sinh tồn.","NASA research tracks sleep patterns in orbit to study spaceflight sleep and support crew health and performance.","NASA theo dõi kiểu ngủ trên quỹ đạo để nghiên cứu giấc ngủ khi bay và hỗ trợ sức khỏe, hiệu suất phi hành đoàn.","Log sleep/wake times and interruptions for several days. Report fatigue that affects tasks.","Ghi giờ ngủ/thức và lần gián đoạn chính trong vài ngày. Báo mệt mỏi ảnh hưởng công việc.",(("NASA — Sleep in Orbit","https://www.nasa.gov/blogs/stationreport/2024/01/25/iss-daily-summary-report-1-25-2024/"),)),
("Radiation exposure","Phơi nhiễm bức xạ","A dosimeter or mission system records an estimate of exposure over a stated period.","Liều kế hoặc hệ thống nhiệm vụ ghi nhận ước tính phơi nhiễm trong một khoảng thời gian.","Crew exposure differs by location and activity. NASA monitors each crew member so mission teams can manage exposure.","Mức phơi nhiễm thay đổi theo vị trí và hoạt động. NASA theo dõi từng thành viên để đội nhiệm vụ quản lý mức phơi nhiễm.","Use the assigned monitor and mission rules. Record unit/date range; exposure cannot be judged by how you feel.","Dùng thiết bị và quy định nhiệm vụ. Ghi đơn vị/khoảng thời gian; không thể biết mức phơi nhiễm chỉ bằng cảm giác.",(("NASA — Space Radiation","https://www.nasa.gov/directorates/esdmd/hhp/space-radiation/"),("NASA — Human-System Standard, Vol. 2","https://www.nasa.gov/reference/6-0-natural-and-induced-environments-vol-2/"))),
("Complete blood count (CBC)","Công thức máu toàn bộ (CBC)","A lab panel counting red cells, white cells, and platelets; it may report hemoglobin and related measures.","Xét nghiệm đếm hồng cầu, bạch cầu, tiểu cầu; có thể kèm hemoglobin và chỉ số liên quan.","Red cells/hemoglobin carry oxygen, white cells support immune defense, and platelets help blood clot.","Hồng cầu/hemoglobin vận chuyển oxy, bạch cầu tham gia miễn dịch, tiểu cầu giúp đông máu.","Check test name, unit, date, and lab reference interval. Ask the medical team to interpret in context.","Kiểm tra tên xét nghiệm, đơn vị, ngày lấy mẫu và khoảng tham chiếu. Nhờ nhân viên y tế diễn giải theo tình trạng của bạn.",(("MedlinePlus — Complete blood count","https://medlineplus.gov/lab-tests/complete-blood-count-cbc/"),)),
)

class HealthMetricGuide(QWidget):
    """Source-linked crew education without flight-specific clinical cutoffs."""
    def __init__(self,locale="en",parent=None):
        super().__init__(parent); self.language="vi" if str(locale).lower().startswith("vi") else "en"
        root=QVBoxLayout(self); root.setContentsMargins(8,6,8,6); root.setSpacing(8)
        self.heading=QLabel(); self.heading.setObjectName("sectionTitle"); root.addWidget(self.heading)
        self.note=QLabel(); self.note.setObjectName("pageHint"); self.note.setWordWrap(True); root.addWidget(self.note)
        scroll=QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        content=QWidget(); cards=QVBoxLayout(content); cards.setContentsMargins(2,2,8,2); cards.setSpacing(9); self.rows=[]
        for m in METRICS:
            card=QFrame(); card.setObjectName("contentPanel"); box=QVBoxLayout(card); box.setContentsMargins(12,10,12,10); box.setSpacing(5)
            title=QLabel(); title.setObjectName("sectionTitle"); title.setWordWrap(True); box.addWidget(title); fields={}
            for key in ("measure","purpose","tip"):
                label=QLabel(); label.setObjectName("eyebrow"); box.addWidget(label)
                body=QLabel(); body.setObjectName("pageHint"); body.setWordWrap(True); box.addWidget(body); fields[key]=(label,body)
            for name,url in m[8]:
                link=QPushButton(name); link.setObjectName("navButton")
                link.clicked.connect(lambda checked=False,target=url: QDesktopServices.openUrl(QUrl(target))); box.addWidget(link)
            cards.addWidget(card); self.rows.append((m,title,fields))
        cards.addStretch(1); scroll.setWidget(content); root.addWidget(scroll,1); self.set_locale(self.language)
    def set_locale(self,locale):
        self.language="vi" if str(locale).lower().startswith("vi") else "en"; copy=COPY[self.language]
        self.heading.setText(copy["intro"]); self.note.setText(copy["note"])
        for m,title,fields in self.rows:
            vi=self.language=="vi"; title.setText(m[1] if vi else m[0])
            for key,offset in (("measure",2),("purpose",4),("tip",6)):
                label,body=fields[key]; label.setText(copy[key]); body.setText(m[offset+(1 if vi else 0)])

class HealthTipDialog(QDialog):
    """Small, non-blocking first-run tip with a simple close action."""
    def __init__(self,locale,open_guide:Callable[[],None],parent=None):
        super().__init__(parent,Qt.WindowType.Dialog|Qt.WindowType.WindowCloseButtonHint)
        self.open_guide=open_guide; self.setModal(False); self.setFixedWidth(390); self.setMinimumHeight(180); self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose,False)
        layout=QVBoxLayout(self); layout.setContentsMargins(16,13,16,15); layout.setSpacing(10)
        self.title=QLabel(); self.title.setObjectName("sectionTitle"); layout.addWidget(self.title)
        self.body=QLabel(); self.body.setObjectName("pageHint"); self.body.setWordWrap(True); layout.addWidget(self.body)
        actions=QHBoxLayout(); actions.addStretch(1)
        self.open_button=QPushButton(); self.open_button.setObjectName("navButton"); self.open_button.clicked.connect(self._open); actions.addWidget(self.open_button)
        self.close_button=QPushButton(); self.close_button.setObjectName("primaryAction"); self.close_button.clicked.connect(self.close); actions.addWidget(self.close_button)
        layout.addLayout(actions); self.set_locale(locale)
    def set_locale(self,locale):
        copy=COPY["vi" if str(locale).lower().startswith("vi") else "en"]
        self.setWindowTitle("AETHERION"); self.title.setText(copy["tip_title"]); self.body.setText(copy["tip_body"])
        self.open_button.setText(copy["tip_open"]); self.close_button.setText(copy["tip_close"]); self.setAccessibleName(copy["close_name"])
    def _open(self):
        self.close(); self.open_guide()

def show_health_tip_once(parent,locale,open_guide):
    settings=QSettings(); key="education/health_metric_tip_shown_v1"
    if settings.value(key,False,type=bool): return None
    settings.setValue(key,True); settings.sync()
    dialog=HealthTipDialog(locale,open_guide,parent); dialog.show(); dialog.raise_(); return dialog
