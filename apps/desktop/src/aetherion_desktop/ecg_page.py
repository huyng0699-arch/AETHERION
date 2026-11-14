"""Native, bilingual ECG view backed only by explicit authenticated real signal exports.

No generated EKG line or automated interpretation. A device-provided CSV is
attested by the operator and remains UNVERIFIED until independently checked.
"""
from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import io
import json
import math
from urllib.parse import quote, urlencode

from PySide6.QtCore import Qt, QUrl, QDateTime, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtNetwork import QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateTimeEdit, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSpinBox,
    QVBoxLayout, QWidget,
)
from .localization import normalize_locale, tr


def parse_ecg_csv(raw: bytes) -> tuple[list[float], str]:
    """Read a real millivolt column without guessing unknown time/units.

    Supports one numeric column or a clearly labelled voltage_mV column. Two
    unlabelled numeric columns are ambiguous and rejected, not silently graphed.
    """
    if len(raw) > 3_500_000:
        raise ValueError('ECG CSV exceeds upload size limit')
    content = raw.decode('utf-8-sig')
    rows = [r for r in csv.reader(io.StringIO(content)) if any(c.strip() for c in r)]
    if not rows:
        raise ValueError('Empty CSV')
    headers = [c.strip().lower().replace(' ', '_') for c in rows[0]]
    labels = {'voltage_mv','ecg_mv','amplitude_mv','millivolts','mv','signal_mv'}
    columns = [i for i,c in enumerate(headers) if c in labels]
    if len(columns) == 1:
        col, body = columns[0], rows[1:]
    elif len(rows[0]) == 1:
        col = 0
        try:
            float(rows[0][0])
            body = rows
        except ValueError:
            if headers[0] not in labels:
                raise ValueError('CSV must explicitly identify the millivolt column')
            body = rows[1:]
    else:
        raise ValueError('Ambiguous CSV: specify a voltage_mV column')
    if len(body) > 100_000:
        raise ValueError('Too many ECG samples')
    values = []
    for row in body:
        if len(row) <= col:
            raise ValueError('Missing voltage in source CSV')
        try:
            voltage = float(row[col].strip())
        except ValueError as exc:
            raise ValueError('Non-numeric voltage sample') from exc
        if not math.isfinite(voltage) or abs(voltage) > 50:
            raise ValueError('Non-finite or out-of-bounds voltage')
        values.append(voltage)
    if not 250 <= len(values) <= 100_000:
        raise ValueError('Need 250–100000 measured samples')
    return values, hashlib.sha256(raw).hexdigest()


class ECGTrace(QWidget):
    """Auto-scaled signal inspection only; grid is not calibrated diagnostic paper."""
    def __init__(self):
        super().__init__()
        self.points = []
        self.sample_rate = 250
        self.setMinimumHeight(285)
        self.accent = QColor('#3185C5')

    def set_signal(self, points, sample_rate):
        self.points = sorted(points, key=lambda p:p['index']) if points else []
        self.sample_rate = sample_rate
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.palette().base())
        rect = self.rect().adjusted(58, 24, -22, -42)
        if rect.width() < 40 or rect.height() < 40:
            return
        muted = self.palette().text().color()
        muted.setAlpha(70)
        painter.setPen(QPen(muted, 1))
        for i in range(5):
            y=int(rect.top()+i*rect.height()/4)
            painter.drawLine(rect.left(),y,rect.right(),y)
        for i in range(9):
            x=int(rect.left()+i*rect.width()/8)
            painter.drawLine(x,rect.top(),x,rect.bottom())
        if not self.points:
            return
        vals = [p['millivolts'] for p in self.points]
        vmin,vmax=min(vals),max(vals)
        span = max(.1,vmax-vmin)
        ymin,ymax=vmin-span*.08,vmax+span*.08
        indices=[p['index'] for p in self.points]
        start,end=min(indices),max(indices)
        if start>=end:return
        points=[(rect.left()+rect.width()*(p['index']-start)/(end-start),
                 rect.bottom()-rect.height()*(p['millivolts']-ymin)/(ymax-ymin)) for p in self.points]
        path=QPainterPath()
        path.moveTo(*points[0])
        for p in points[1:]: path.lineTo(*p)
        painter.setPen(QPen(self.accent,2.1))
        painter.drawPath(path)
        painter.setPen(QPen(muted,1))
        painter.drawText(4,rect.top()+10,f'{ymax:.2f} mV')
        painter.drawText(4,rect.bottom(),f'{ymin:.2f} mV')
        painter.drawText(rect.left(),rect.bottom()+28,f'{start/self.sample_rate:.2f} s')
        painter.drawText(rect.right()-95,rect.bottom()+28,f'{end/self.sample_rate:.2f} s')


class ECGPage(QWidget):
    open_mission = Signal()

    def __init__(self, api_url, network, locale='vi', parent=None):
        super().__init__(parent)
        self.api_url=api_url.rstrip('/')
        self.network=network
        self.locale=normalize_locale(locale)
        self.subject_id=''
        self.token=''
        self.file_samples=[]
        self.original_digest=''
        self._serial=0
        self._records=[]
        outside=QVBoxLayout(self);outside.setContentsMargins(0,0,0,0)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.Shape.NoFrame)
        outside.addWidget(scroll)
        body=QWidget();scroll.setWidget(body)
        self.body=QVBoxLayout(body);self.body.setContentsMargins(28,24,28,30);self.body.setSpacing(17)
        self.title=QLabel();self.title.setObjectName('heroTitle');self.body.addWidget(self.title)
        self.subtitle=QLabel();self.subtitle.setObjectName('heroCopy');self.subtitle.setWordWrap(True);self.body.addWidget(self.subtitle)
        banner=QFrame();banner.setObjectName('surface');r=QHBoxLayout(banner)
        self.identity=QLabel();self.identity.setObjectName('pageHint');self.identity.setWordWrap(True);r.addWidget(self.identity,1)
        self.auth_button=QPushButton();self.auth_button.clicked.connect(self.open_mission.emit);r.addWidget(self.auth_button)
        self.refresh_button=QPushButton();self.refresh_button.clicked.connect(self.refresh);r.addWidget(self.refresh_button)
        self.body.addWidget(banner)
        self.status=QLabel();self.status.setObjectName('pageHint');self.status.setWordWrap(True);self.body.addWidget(self.status)
        wave=QFrame();wave.setObjectName('surface');v=QVBoxLayout(wave)
        self.wave_title=QLabel();self.wave_title.setObjectName('heading');v.addWidget(self.wave_title)
        self.plot=ECGTrace();v.addWidget(self.plot)
        self.signal_info=QLabel();self.signal_info.setObjectName('pageHint');self.signal_info.setWordWrap(True);v.addWidget(self.signal_info)
        self.body.addWidget(wave)
        list_frame=QFrame();list_frame.setObjectName('surface');ll=QVBoxLayout(list_frame)
        self.list_label=QLabel();self.list_label.setObjectName('heading');ll.addWidget(self.list_label)
        self.list_widget=QListWidget();self.list_widget.setMaximumHeight(180)
        self.list_widget.itemActivated.connect(self.select_record)
        self.list_widget.itemClicked.connect(self.select_record)
        ll.addWidget(self.list_widget)
        self.body.addWidget(list_frame)
        upload=QFrame();upload.setObjectName('surface');ul=QVBoxLayout(upload)
        self.import_label=QLabel();self.import_label.setObjectName('heading');ul.addWidget(self.import_label)
        self.import_help=QLabel();self.import_help.setObjectName('pageHint');self.import_help.setWordWrap(True);ul.addWidget(self.import_help)
        src=QHBoxLayout();self.source_id=QLineEdit();self.source_id.setMaxLength(120)
        src.addWidget(self.source_id,1)
        self.browse=QPushButton();self.browse.clicked.connect(self.choose_file);src.addWidget(self.browse)
        ul.addLayout(src)
        details=QHBoxLayout()
        self.lead=QComboBox()
        for lead in ('I','II','III','aVR','aVL','aVF',*(f'V{i}' for i in range(1,7)),'single'):
            self.lead.addItem(lead)
        self.lead.setCurrentText('II');details.addWidget(self.lead)
        self.hz=QSpinBox();self.hz.setRange(50,2000);self.hz.setValue(250);self.hz.setSuffix(' Hz');details.addWidget(self.hz)
        self.observed_at=QDateTimeEdit(QDateTime.currentDateTime());self.observed_at.setCalendarPopup(True)
        self.observed_at.setDisplayFormat('yyyy-MM-dd HH:mm:ss');details.addWidget(self.observed_at)
        details.addStretch();ul.addLayout(details)
        self.attest=QCheckBox();self.attest.setChecked(False);ul.addWidget(self.attest)
        self.upload_button=QPushButton();self.upload_button.setObjectName('primaryAction');self.upload_button.clicked.connect(self.upload);ul.addWidget(self.upload_button)
        self.body.addWidget(upload)
        self.body.addStretch()
        self.set_locale(self.locale)
        self._reset_private()

    def t(self,key,**fmt):return tr(self.locale,'ecg.'+key,**fmt)

    def set_locale(self,locale):
        self.locale=normalize_locale(locale)
        for attr,key in (('title','title'),('subtitle','subtitle'),('auth_button','authorize'),('refresh_button','refresh'),
                         ('wave_title','wave_title'),('list_label','list'),('import_label','import'),
                         ('import_help','import_help'),('browse','browse'),('attest','attest'),('upload_button','upload')):
            getattr(self,attr).setText(self.t(key))
        self.source_id.setPlaceholderText(self.t('source_placeholder'))
        self.identity.setText(self.t('subject',subject=self.subject_id) if self.subject_id else self.t('no_subject'))
        if not self.plot.points:self.signal_info.setText(self.t('no_waveform'))

    def _reset_private(self):
        self._serial+=1
        self.list_widget.clear();self.plot.set_signal([],250)
        self.file_samples=[];self.original_digest='';self.attest.setChecked(False)
        self.signal_info.setText(self.t('no_waveform'))
        self.status.setText(self.t('denied') if not self.token else self.t('no_data'))

    def select_subject(self,subject_id,access_token):
        self._reset_private()
        self.subject_id='';self.token=''
        if not subject_id or len(subject_id)>80 or not access_token:
            self.identity.setText(self.t('no_subject'))
            return
        self.subject_id=subject_id;self.token=access_token
        self.identity.setText(self.t('subject',subject=subject_id))
        self.refresh()

    def _request(self,url,body=None,callback=None):
        req=QNetworkRequest(QUrl(url))
        req.setRawHeader(b'Authorization',('Bearer '+self.token).encode('utf-8'))
        req.setTransferTimeout(20000)
        if body is not None:
            req.setRawHeader(b'Content-Type',b'application/json')
            reply=self.network.post(req,json.dumps(body,ensure_ascii=False).encode('utf-8'))
        else:reply=self.network.get(req)
        self._serial+=1;serial=self._serial
        if callback:reply.finished.connect(lambda:callback(reply,serial))

    def refresh(self):
        self._serial+=1;self.plot.set_signal([],self.hz.value());self.list_widget.clear()
        if not self.token or not self.subject_id:
            self.status.setText(self.t('denied'));return
        self.status.setText(self.t('loading'))
        url=self.api_url+'/api/v1/ecg/recordings?'+urlencode({'subject_id':self.subject_id})
        self._request(url,callback=self._listed)

    def _listed(self,reply,serial):
        code=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw=bytes(reply.readAll());reply.deleteLater()
        if serial!=self._serial:return
        if code in (401,403):
            self.token='';self._reset_private();self.status.setText(self.t('denied'));return
        try:
            if code!=200:raise ValueError('Unauthorized or offline')
            data=json.loads(raw.decode('utf-8'))
            if not isinstance(data,dict) or data.get('subject_id')!=self.subject_id or not isinstance(data.get('recordings'),list):
                raise ValueError('Identity mismatch')
            self._records=data['recordings']
            for meta in self._records:
                if meta.get('subject_id')!=self.subject_id:raise ValueError('Cross-identity payload')
                rid=meta.get('recording_id','')
                if not isinstance(rid,str) or not rid.startswith('ecg-'):raise ValueError('Invalid ID')
                text=f"{str(meta.get('recorded_at',''))[:19]}  ·  {meta.get('lead_name')}  ·  {meta.get('source_id')}"
                item=QListWidgetItem(text);item.setData(Qt.ItemDataRole.UserRole,rid);self.list_widget.addItem(item)
            self.status.setText(self.t('count',count=self.list_widget.count()))
        except (ValueError,TypeError,UnicodeError):
            self.status.setText(self.t('offline'))

    def select_record(self,item):
        if not self.token:return
        rid=item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(rid,str) or not rid.startswith('ecg-'):return
        url=self.api_url+'/api/v1/ecg/recordings/'+quote(rid,safe='')+'?'+urlencode({'subject_id':self.subject_id,'max_points':2400})
        self.status.setText(self.t('loading'))
        self._request(url,callback=self._loaded)

    def _loaded(self,reply,serial):
        code=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw=bytes(reply.readAll());reply.deleteLater()
        if serial!=self._serial:return
        if code in (401,403):
            self.token='';self._reset_private();self.status.setText(self.t('denied'));return
        try:
            if code!=200:raise ValueError('Unavailable recording')
            data=json.loads(raw.decode('utf-8'));meta=data.get('recording')
            if not isinstance(meta,dict) or meta.get('subject_id')!=self.subject_id or not isinstance(data.get('points'),list):
                raise ValueError('Malformed waveform response')
            rows=data['points'];rate=float(meta['sample_rate_hz'])
            if len(rows)>5000 or not (50<=rate<=2000):raise ValueError('Invalid rate')
            signal=[]
            for row in rows:
                index=row['index'];voltage=row['millivolts']
                if not isinstance(index,int) or not isinstance(voltage,(int,float)) or not math.isfinite(voltage):
                    raise ValueError('Invalid sample')
                signal.append({'index':index,'millivolts':float(voltage)})
            self.plot.set_signal(signal,rate)
            self.signal_info.setText(self.t('loaded',lead=meta.get('lead_name',''),
                source=meta.get('source_id',''),n=meta.get('sample_count',0),
                quality=meta.get('verification_state','UNVERIFIED')))
            self.status.setText(self.t('display_only'))
        except (ValueError,KeyError,TypeError,UnicodeError):
            self.plot.set_signal([],250);self.status.setText(self.t('offline'))

    def choose_file(self):
        filename,_=QFileDialog.getOpenFileName(self,self.t('browse'),'', 'CSV (*.csv *.txt)')
        if not filename:return
        try:
            with open(filename,'rb') as f:raw=f.read(3_500_001)
            self.file_samples,self.original_digest=parse_ecg_csv(raw)
            self.status.setText(self.t('selected',count=len(self.file_samples)))
        except (OSError,ValueError,UnicodeError) as exc:
            self.file_samples=[];self.original_digest=''
            self.status.setText(self.t('invalid_file')+' ('+str(exc)[:100]+')')

    def upload(self):
        if not self.token or not self.subject_id:
            self.status.setText(self.t('denied'));return
        if not self.file_samples or not self.source_id.text().strip() or not self.attest.isChecked():
            self.status.setText(self.t('required'));return
        if len(self.file_samples)/self.hz.value()>120:
            self.status.setText(self.t('invalid_file'));return
        observed=self.observed_at.dateTime().toString(Qt.DateFormat.ISODateWithMs)
        body={'subject_id':self.subject_id,'source_id':self.source_id.text().strip(),
              'recorded_at':observed,'lead_name':self.lead.currentText(),
              'sample_rate_hz':self.hz.value(),'samples_millivolts':self.file_samples,
              'sample_origin':'DEVICE_IMPORT','attested_real_signal':True,
              'original_source_sha256':self.original_digest}
        self.status.setText(self.t('uploading'))
        self._request(self.api_url+'/api/v1/ecg/recordings',body,self._uploaded)

    def _uploaded(self,reply,serial):
        code=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw=bytes(reply.readAll());reply.deleteLater()
        if serial!=self._serial:return
        if code in (401,403):
            self.token='';self._reset_private();self.status.setText(self.t('denied'));return
        if code!=201:
            self.status.setText(self.t('upload_error')+f' (HTTP {code})');return
        try:
            payload=json.loads(raw.decode('utf-8'))
            if payload.get('recording',{}).get('subject_id')!=self.subject_id:raise ValueError('subject mismatch')
            self.file_samples=[];self.original_digest='';self.attest.setChecked(False)
            self.status.setText(self.t('uploaded'))
            self.refresh()
        except (ValueError,TypeError,UnicodeError):
            self.status.setText(self.t('upload_error'))
