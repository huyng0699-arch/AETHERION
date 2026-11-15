"""AETHERION native chat: real model only, no canned assistant replies.

Messages and bearer token remain in memory for this window session. Model and
Cloud policy are reported by Server; no API secret ever enters Desktop.
"""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor
from PySide6.QtNetwork import QNetworkRequest
from PySide6.QtWidgets import (QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget,
                               QMessageBox)

from .localization import normalize_locale, tr


class ChatPage(QWidget):
    authorization_requested = Signal()
    open_symptom = Signal()
    open_library = Signal()

    def __init__(self, api_url, network, locale='vi', parent=None):
        super().__init__(parent)
        self.api_url=api_url.rstrip('/')
        self.network=network
        self.locale=normalize_locale(locale)
        self._token=''
        self._identity=''
        self._seq={'status':0,'chat':0}
        self._chat_pending=False
        self._source_context=None
        self.messages=[]
        self.local_ok=False
        self.cloud_ok=False
        self.last_model=''
        root=QVBoxLayout(self)
        root.setContentsMargins(28,20,28,25)
        root.setSpacing(11)
        self.title=QLabel();self.title.setObjectName('heroTitle');root.addWidget(self.title)
        self.intro=QLabel();self.intro.setObjectName('heroCopy');self.intro.setWordWrap(True);root.addWidget(self.intro)
        actions=QFrame();actions.setObjectName('surface');top=QHBoxLayout(actions)
        self.auth=QPushButton();self.auth.clicked.connect(self.authorization_requested.emit)
        top.addWidget(self.auth)
        self.provider=QComboBox();self.provider.currentIndexChanged.connect(self._provider_changed)
        top.addWidget(self.provider)
        self.refresh=QPushButton();self.refresh.clicked.connect(self.refresh_status)
        top.addWidget(self.refresh)
        self.symptoms=QPushButton();self.symptoms.clicked.connect(self.open_symptom.emit)
        top.addWidget(self.symptoms)
        self.library=QPushButton();self.library.clicked.connect(self.open_library.emit)
        top.addWidget(self.library)
        top.addStretch()
        root.addWidget(actions)
        self.status=QLabel();self.status.setObjectName('pageHint');self.status.setWordWrap(True);root.addWidget(self.status)
        self.source_row=QFrame();self.source_row.setObjectName('surface');source_layout=QHBoxLayout(self.source_row)
        self.source_context_label=QLabel();self.source_context_label.setWordWrap(True);source_layout.addWidget(self.source_context_label,1)
        self.source_clear=QPushButton();self.source_clear.clicked.connect(self.clear_source_context);source_layout.addWidget(self.source_clear)
        self.source_row.hide();root.addWidget(self.source_row)
        self.chat_scroll=QScrollArea();self.chat_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setMinimumHeight(250)
        self.chat_content=QWidget();self.chat_scroll.setWidget(self.chat_content)
        self.chat_layout=QVBoxLayout(self.chat_content);self.chat_layout.setContentsMargins(8,10,8,10)
        self.chat_layout.setSpacing(13);self.chat_layout.addStretch(1)
        root.addWidget(self.chat_scroll,1)
        compose=QFrame();compose.setObjectName('surface');c=QVBoxLayout(compose)
        self.editor=QTextEdit();self.editor.setAcceptRichText(False)
        self.editor.setMaximumHeight(95);self.editor.setMinimumHeight(66)
        c.addWidget(self.editor)
        bottom=QHBoxLayout()
        self.cloud_consent=QCheckBox();self.cloud_consent.hide();bottom.addWidget(self.cloud_consent)
        self.clear_button=QPushButton();self.clear_button.clicked.connect(self.clear_chat);bottom.addWidget(self.clear_button)
        bottom.addStretch()
        self.send=QPushButton();self.send.setObjectName('primaryAction');self.send.clicked.connect(self.submit)
        bottom.addWidget(self.send)
        c.addLayout(bottom);root.addWidget(compose)
        self.warning=QLabel();self.warning.setObjectName('pageHint');self.warning.setWordWrap(True);root.addWidget(self.warning)
        self.set_locale(self.locale)
        self.refresh_status()

    def t(self,key,**kwargs):return tr(self.locale,'chat.'+key,**kwargs)

    def set_locale(self,locale):
        self.locale=normalize_locale(locale)
        for name,key in [('title','title'),('intro','intro'),('auth','authorize'),
                         ('refresh','refresh'),('symptoms','symptoms'),('library','library'),
                         ('clear_button','clear'),('send','send'),('cloud_consent','cloud_consent'),('warning','warning')]:
            getattr(self,name).setText(self.t(key))
        self.source_clear.setText('Clear source' if self.locale=='en' else 'Xoa nguon')
        self.provider.blockSignals(True)
        selection=self.provider.currentData()
        self.provider.clear()
        self.provider.addItem(self.t('local'), 'local')
        self.provider.addItem(self.t('cloud'), 'cloud')
        self.provider.setCurrentIndex(max(0,self.provider.findData(selection)))
        self.provider.blockSignals(False)
        self.editor.setPlaceholderText(self.t('placeholder'))
        self._update_actions()

    def set_identity(self,subject_id,access_token):
        # No cross-user conversation leakage, even if the same window stays open.
        if subject_id!=self._identity or access_token!=self._token:
            self._seq['status']+=1
            self.clear_source_context()
        self._identity=subject_id if access_token else ''
        self._token=access_token or ''
        self.refresh_status()

    def _request(self,method,route,payload,callback,scope='status'):
        req=QNetworkRequest(QUrl(self.api_url+route))
        req.setTransferTimeout(30000)
        if self._token:
            req.setRawHeader(b'Authorization',('Bearer '+self._token).encode('utf-8'))
        if method=='POST':
            req.setRawHeader(b'Content-Type',b'application/json')
            reply=self.network.post(req,json.dumps(payload,ensure_ascii=False).encode('utf-8'))
        else:reply=self.network.get(req)
        self._seq[scope]+=1;seq=self._seq[scope]
        reply.finished.connect(lambda:callback(reply,seq))

    def refresh_status(self):
        self.local_ok=self.cloud_ok=False
        self._update_actions()
        if not self._token:
            self.status.setText(self.t('no_auth'))
            return
        self.status.setText(self.t('checking'))
        self._request('GET','/api/v1/assistant/status',None,self._status_loaded,scope='status')

    def _status_loaded(self,reply,seq):
        code=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw=bytes(reply.readAll());reply.deleteLater()
        if seq!=self._seq['status']:return
        if code==401:
            self._token='';self._identity='';self.clear_source_context()
            self.status.setText(self.t('no_auth'));return
        try:
            if code!=200:raise ValueError('unavailable')
            body=json.loads(raw.decode('utf-8'))
            self.local_ok=body.get('local_available') is True
            self.cloud_ok=body.get('cloud_available') is True
            self.last_model=str(body.get('local_model') or body.get('cloud_model') or '')
            self.status.setText(self.t('models',local=self.t('ready') if self.local_ok else self.t('unavailable'),
                                           cloud=self.t('ready') if self.cloud_ok else self.t('unavailable')))
        except (UnicodeError,ValueError,TypeError):
            self.status.setText(self.t('offline'))
        self._update_actions()

    def _provider_changed(self,*_):
        self.cloud_consent.setChecked(False)
        self._update_actions()

    def _update_actions(self):
        provider=self.provider.currentData()
        self.cloud_consent.setVisible(provider=='cloud')
        ready=self.local_ok if provider=='local' else self.cloud_ok
        self.provider.setEnabled(not self._chat_pending)
        self.cloud_consent.setEnabled(not self._chat_pending)
        self.send.setEnabled(bool(self._token and ready and not self._chat_pending))
        self.editor.setEnabled(bool(self._token and not self._chat_pending))
        self.source_clear.setEnabled(not self._chat_pending)

    def _bubble(self,role,text,sources=None):
        panel=QFrame();panel.setObjectName('surface')
        wrap=QVBoxLayout(panel);wrap.setContentsMargins(17,12,17,13)
        header=QLabel(self.t('user_label') if role=='user' else self.t('ai_label'))
        header.setObjectName('eyebrow');wrap.addWidget(header)
        content=QLabel(text)
        content.setTextFormat(Qt.TextFormat.PlainText)
        content.setWordWrap(True);content.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        wrap.addWidget(content)
        if role=='assistant' and isinstance(sources,list):
            for source in sources:
                if not isinstance(source,dict):continue
                title=str(source.get('title') or source.get('source_id') or 'NASA source')
                url=str(source.get('url') or '')
                claim=str(source.get('source_claim') or 'UNKNOWN')
                state=str(source.get('content_state') or 'UNKNOWN')
                provenance=QLabel(f"Source: {title}\n{url}\nArchive claim: {claim}; content: {state}; original PDF not independently checked.")
                provenance.setObjectName('pageHint');provenance.setWordWrap(True)
                provenance.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                wrap.addWidget(provenance)
        self.chat_layout.insertWidget(max(0,self.chat_layout.count()-1),panel)
        self.chat_scroll.verticalScrollBar().setValue(self.chat_scroll.verticalScrollBar().maximum())

    def submit(self):
        prompt=self.editor.toPlainText().strip()
        provider=self.provider.currentData()
        if not self._token or not prompt or self._chat_pending:return
        ready=self.local_ok if provider=='local' else self.cloud_ok
        if not ready:
            self.status.setText(self.t('model_missing'));return
        if provider=='cloud':
            if not self.cloud_consent.isChecked():
                self.status.setText(self.t('consent_required'));return
            accepted=QMessageBox.question(self,self.t('cloud'),self.t('confirm_cloud'),
                         QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No)
            if accepted!=QMessageBox.StandardButton.Yes:return
        if len(prompt)>3000:
            self.status.setText(self.t('too_long'));return
        self.messages.append({'role':'user','content':prompt})
        self.messages=self.messages[-15:]
        self._bubble('user',prompt)
        self.editor.clear()
        self._chat_pending=True
        self._update_actions()
        self.status.setText(self.t('thinking'))
        bounded=[{'role':line['role'],'content':line['content'][:3000]} for line in self.messages[-16:]]
        while len(bounded)>1 and sum(len(line['content']) for line in bounded)>12000:
            bounded.pop(0)
        payload={'messages':bounded,'provider':provider,
                 'cloud_consent':bool(provider=='cloud' and self.cloud_consent.isChecked()),'locale':self.locale}
        if self._source_context:
            payload['source_article_id']=self._source_context['article_id']
        self._request('POST','/api/v1/assistant/chat',payload,self._answered,scope='chat')

    def _answered(self,reply,seq):
        code=reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw=bytes(reply.readAll());reply.deleteLater()
        if seq!=self._seq['chat']:return
        try:
            if code!=200:raise ValueError('model not available')
            data=json.loads(raw.decode('utf-8'))
            answer=data.get('reply')
            if not isinstance(answer,str) or not answer.strip() or data.get('stored_by_server') is not False:
                raise ValueError('invalid model response')
            self.messages.append({'role':'assistant','content':answer})
            self._bubble('assistant',answer,data.get('sources'))
            self.status.setText(self.t('answered',provider=data.get('provider','')))
        except (UnicodeError,ValueError,TypeError):
            # A failed model request cannot leave a fake assistant turn in the chat.
            if self.messages and self.messages[-1]['role']=='user':
                self.messages.pop()
            self.status.setText(self.t('model_error'))
        finally:
            self._chat_pending=False
            self._update_actions()

    def set_source_context(self,article_id,title):
        stable_id=str(article_id or '')
        if len(stable_id)!=9 or not stable_id.startswith('CLIFF-') or not stable_id[6:].isdigit():
            self.clear_source_context()
            return
        if not self._source_context or self._source_context.get('article_id')!=stable_id:
            self.clear_chat()
        self._source_context={'article_id':stable_id,'title':str(title or stable_id)[:240]}
        self.source_context_label.setText(f"NASA source attached to chat  ·  {self._source_context['title']}  ·  {stable_id}")
        self.source_row.show()
        self._update_actions()

    def clear_source_context(self):
        self._source_context=None
        self.source_context_label.clear()
        self.source_row.hide()
        self.clear_chat()

    def clear_chat(self):
        self._seq['chat']+=1
        self._chat_pending=False
        self.messages.clear()
        while self.chat_layout.count()>1:
            item=self.chat_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        self.editor.clear()
        self.cloud_consent.setChecked(False)
        self._update_actions()

