"""AETHERION native anatomy viewer: genuine verified 3D geometry, never a 2D stand-in.

Only approved, checksum-matched educational meshes may be rendered. Source-tree
bundles work offline; packaged clients can ask the canonical AETHERION Server
for the very same content. No medical diagnosis or treatment inference.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from PySide6.QtCore import QStandardPaths, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (QComboBox, QFrame, QHBoxLayout, QLabel, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget)
from shiboken6 import isValid

from .localization import normalize_locale
from .runtime_paths import reference_path

ROOT = Path(__file__).resolve().parents[4]
_RUNTIME_MANIFEST = reference_path('anatomy', 'approved_models.json')
MANIFEST = _RUNTIME_MANIFEST if _RUNTIME_MANIFEST.is_file() else (ROOT / 'knowledge' / 'anatomy' / 'approved_models.json')
ASSETS = MANIFEST.parent
VALID_ID = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
SUPPORTED = {'.stl', '.obj', '.ply', '.vtk', '.vtp', '.vtu'}
MAX_ASSET_BYTES = 40 * 1024 * 1024

UI = {
 'vi': {'title':'Bản đồ giải phẫu 3D','subtitle':'Mô hình hình học thật, có nguồn và giấy phép. Xoay, phóng to, di chuyển và chọn vùng trên mesh.',
        'choose':'Chọn cấu trúc','reload':'Tải danh mục từ Server','reset':'Đặt lại góc nhìn',
        'source':'Mở nguồn gốc','inspect':'Chi tiết nguồn','empty':'Chưa có mô hình hợp lệ được duyệt hoặc không truy cập được Server. Không dựng hình giải phẫu giả.',
        'install':'Cài gói aetherion-desktop[atlas] để bật PyVistaQt / VTK trên Windows.',
        'loading':'Đang kiểm tra mô hình, giấy phép và SHA-256…','invalid':'Tệp 3D không khớp SHA-256 hoặc vượt kích thước cho phép.',
        'ready':'Đang hiển thị {name} • {n} điểm, {cells} mặt. Kéo để xoay, cuộn để phóng to, chuột phải để di chuyển.',
        'selected':'Đã chọn {name}. Mô hình chỉ dùng cho giáo dục, chưa xác thực vị trí lâm sàng.',
        'license':'Bản quyền mô hình: {author} • {license} • Chỉ cho học tập, không dùng để chẩn đoán.',
        'network':'Server không trả danh mục 3D hợp lệ; tiếp tục dùng những mô hình đã kiểm chứng trên máy.'},
 'en': {'title':'3D Anatomy Atlas','subtitle':'Genuine licensed geometry. Rotate, zoom, pan, and select the mesh; source evidence stays visible.',
        'choose':'Anatomical structure','reload':'Refresh from Server','reset':'Reset camera',
        'source':'Open original source','inspect':'Source details','empty':'No approved, verified anatomical geometry is available locally or from Server. No fake anatomical meshes.',
        'install':'Install aetherion-desktop[atlas] to enable native PyVistaQt / VTK on Windows.',
        'loading':'Checking model, rights and SHA-256…','invalid':'Geometry hash mismatch or excessive asset size. Model rejected.',
        'ready':'Displaying {name} • {n} points, {cells} cells. Drag to orbit, scroll to zoom, right-drag to pan.',
        'selected':'Selected {name}. Educational geometry only; not a clinically validated region selection.',
        'license':'Model credit: {author} • {license} • Educational use only, not for diagnosis.',
        'network':'Server catalog unavailable/invalid; retaining verified local models.'}
}


def approved_models() -> list[dict]:
    """Fail-closed inspection of bundled, original anatomical mesh data."""
    try:
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return []
    root = ASSETS.resolve()
    result = []
    for item in manifest.get('models', []):
        if not isinstance(item, dict) or item.get('rights_status') != 'APPROVED':
            continue
        name, digest = item.get('filename'), item.get('sha256')
        if not isinstance(name, str) or not isinstance(digest, str) or not re.fullmatch('[a-fA-F0-9]{64}', digest):
            continue
        identity = item.get('anatomical_id', '')
        if not isinstance(identity, str) or not VALID_ID.fullmatch(identity):
            continue
        if not all(isinstance(item.get(k), str) and item[k].strip() for k in
                   ('source_url', 'author', 'license', 'derivative_license')):
            continue
        model = (ASSETS / name).resolve()
        if not model.is_relative_to(root) or model.suffix.lower() not in SUPPORTED:
            continue
        if not model.is_file() or model.stat().st_size > MAX_ASSET_BYTES:
            continue
        if hashlib.sha256(model.read_bytes()).hexdigest() != digest.lower():
            continue
        result.append({**item, 'resolved_path': str(model)})
    return result


class BodyAtlas3D(QWidget):
    """Qt-native VTK viewport with validated local assets and optional HTTP catalog."""

    def __init__(self, parent=None, *, api_url='http://127.0.0.1:8765', network=None, locale='vi'):
        super().__init__(parent)
        self.locale = normalize_locale(locale)
        self.api_url = api_url.rstrip('/')
        self.network = network or QNetworkAccessManager(self)
        self.models = {v['anatomical_id']: v for v in approved_models()}
        self.viewer = None
        self.fallback_2d = None  # real 2D list, only when native 3D is unavailable
        self._active_id = ''
        self._request_seq = 0
        self._pending_reply = None
        self.setObjectName('aetherionAtlas3D')

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 19, 28, 25)
        layout.setSpacing(14)
        header = QLabel()
        header.setObjectName('heroTitle')
        self.title = header
        layout.addWidget(header)
        self.description = QLabel()
        self.description.setObjectName('heroCopy')
        self.description.setWordWrap(True)
        layout.addWidget(self.description)
        toolbar = QFrame()
        toolbar.setObjectName('surface')
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 10, 14, 10)
        toolbar_layout.setSpacing(8)
        selector_row = QHBoxLayout()
        selector_row.setSpacing(8)
        self.label = QLabel()
        selector_row.addWidget(self.label)
        self.selector = QComboBox()
        self.selector.setMinimumWidth(140)
        self.selector.setMinimumContentsLength(12)
        self.selector.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.selector.currentIndexChanged.connect(self._select)
        selector_row.addWidget(self.selector, 1)
        toolbar_layout.addLayout(selector_row)
        controls = QHBoxLayout()
        controls.setSpacing(8)
        self.load_button = QPushButton()
        self.load_button.clicked.connect(self.refresh_catalog)
        controls.addWidget(self.load_button)
        self.reset_button = QPushButton()
        self.reset_button.clicked.connect(self.reset_camera)
        controls.addWidget(self.reset_button)
        self.source_button = QPushButton()
        self.source_button.clicked.connect(self.open_source)
        controls.addWidget(self.source_button)
        self.inspect_button = QPushButton()
        self.inspect_button.clicked.connect(self.show_source_inspector)
        controls.addWidget(self.inspect_button)
        controls.addStretch(1)
        toolbar_layout.addLayout(controls)
        layout.addWidget(toolbar)

        self.content = QVBoxLayout()
        self.empty = QLabel()
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setObjectName('pageHint')
        self.empty.setWordWrap(True)
        self.empty.setMinimumHeight(310)
        self.content.addWidget(self.empty, 1)
        layout.addLayout(self.content, 1)
        self.status = QLabel()
        self.status.setObjectName('pageHint')
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.status)
        self.credit = QLabel()
        self.credit.setObjectName('pageHint')
        self.credit.setWordWrap(True)
        self.credit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.credit)

        self.set_locale(self.locale)
        self._populate()
        if self.models:
            self._select()
        else:
            self.refresh_catalog()

    def t(self, key, **fmt):
        return UI[self.locale][key].format(**fmt)

    def set_locale(self, locale):
        self.locale = normalize_locale(locale)
        self.title.setText(self.t('title'))
        self.description.setText(self.t('subtitle'))
        self.label.setText(self.t('choose'))
        self.selector.setAccessibleName(self.t('choose'))
        self.load_button.setText(self.t('reload'))
        self.reset_button.setText(self.t('reset'))
        self.reset_button.setAccessibleName(self.t('reset'))
        self.source_button.setText(self.t('source'))
        self.inspect_button.setText(self.t('inspect'))
        self.inspect_button.setAccessibleName(self.t('inspect'))
        if self.fallback_2d is not None:
            self.fallback_2d.set_locale(self.locale)
        if not self._active_id:
            self.empty.setText(self.t('empty'))
        for i in range(self.selector.count()):
            identity = self.selector.itemData(i)
            meta = self.models.get(identity, {})
            name = meta.get('title_vi' if self.locale == 'vi' else 'title_en')
            self.selector.setItemText(i, str(name or str(identity).replace('_', ' ').title()))

    def _populate(self):
        active = self._active_id
        self.selector.blockSignals(True)
        self.selector.clear()
        for identity, meta in sorted(self.models.items()):
            title = meta.get('title_vi' if self.locale == 'vi' else 'title_en') or identity.replace('_', ' ').title()
            self.selector.addItem(str(title), identity)
        self.selector.blockSignals(False)
        ix = self.selector.findData(active)
        self.selector.setCurrentIndex(ix if ix >= 0 else (0 if self.models else -1))
        self.source_button.setEnabled(bool(self.models))
        self.inspect_button.setEnabled(bool(self.models))
        self.reset_button.setEnabled(self.viewer is not None)

    def refresh_catalog(self):
        self._request_seq += 1
        seq = self._request_seq
        if self._pending_reply is not None and isValid(self._pending_reply):
            self._pending_reply.abort()
        req = QNetworkRequest(QUrl(self.api_url + '/api/v1/knowledge/anatomy/models'))
        req.setTransferTimeout(2500)
        req.setRawHeader(b'Connection', b'close')
        reply = self.network.get(req)
        self._pending_reply = reply
        self.status.setText(self.t('loading'))
        reply.finished.connect(lambda: self._got_catalog(reply, seq))

    def _got_catalog(self, reply, seq):
        if not isValid(reply):
            return
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        data = bytes(reply.readAll())
        reply.deleteLater()
        if not isValid(self):
            return
        if self._pending_reply is reply:
            self._pending_reply = None
        if seq != self._request_seq:
            return
        try:
            if code != 200 or len(data) > 300_000:
                raise ValueError('No trusted catalog')
            catalog = json.loads(data.decode('utf-8'))
            if not isinstance(catalog.get('models'), list):
                raise ValueError('Invalid catalog')
            for item in catalog['models']:
                if not isinstance(item, dict) or item.get('rights_status') != 'APPROVED':
                    continue
                ident, digest = item.get('anatomical_id'), item.get('sha256')
                if not isinstance(ident, str) or not VALID_ID.fullmatch(ident):
                    continue
                if not isinstance(digest, str) or not re.fullmatch('[0-9a-fA-F]{64}', digest):
                    continue
                if item.get('content_type') not in ('model/stl', 'model/obj', 'application/x-ply'):
                    continue
                if not all(isinstance(item.get(k), str) and item[k].strip() for k in ('source_url','author','license')):
                    continue
                size = item.get('size_bytes')
                if not isinstance(size, int) or not (84 <= size <= MAX_ASSET_BYTES):
                    continue
                # Never import a server-chosen local path into the native
                # viewer. Only approved_models() may create resolved_path.
                # Server models are downloaded to an app-owned cache and
                # their SHA-256 must match before VTK sees the file.
                allowed = (
                    'anatomical_id', 'sha256', 'content_type', 'size_bytes',
                    'rights_status', 'source_url', 'author', 'license',
                    'derivative_license', 'citation', 'version',
                    'original_git_blob', 'title_vi', 'title_en', 'filename',
                )
                self.models.setdefault(
                    ident, {key: item[key] for key in allowed if key in item}
                )
            self._populate()
            if not self._active_id and self.models:
                self._select()
            elif not self.models:
                self.status.setText(self.t('empty'))
        except (ValueError, UnicodeError, AttributeError, TypeError):
            self.status.setText(self.t('network'))

    def _select(self, *_):
        identity = self.selector.currentData()
        if not identity or identity not in self.models:
            self._active_id = ''
            self.empty.setText(self.t('empty'))
            return
        self._active_id = identity
        meta = self.models[identity]
        self.credit.setText(self.t('license', author=meta.get('author',''), license=meta.get('license','')))
        path = meta.get('resolved_path')
        if path:
            from .render3d.source_inspector import verified_local_model_file
            verified_file = verified_local_model_file(meta, ASSETS)
            if verified_file is None:
                self.status.setText(self.t('invalid'))
                return
            self._render(verified_file, identity)
            return
        ext = {'model/stl': '.stl', 'model/obj': '.obj', 'application/x-ply': '.ply'}.get(
            meta.get('content_type', 'model/stl'), '.stl')
        filename = identity + ext
        cache = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        if not cache:
            self.status.setText(self.t('invalid'))
            return
        location = Path(cache) / 'verified_anatomy' / filename
        if location.is_file() and location.stat().st_size <= MAX_ASSET_BYTES and hashlib.sha256(location.read_bytes()).hexdigest() == meta['sha256']:
            self._render(location, identity)
            return
        self.status.setText(self.t('loading'))
        if self._pending_reply is not None and isValid(self._pending_reply):
            self._pending_reply.abort()
        req = QNetworkRequest(QUrl(self.api_url + '/api/v1/knowledge/anatomy/models/' + identity + '/file'))
        req.setTransferTimeout(5000)
        req.setRawHeader(b'Connection', b'close')
        reply = self.network.get(req)
        self._pending_reply = reply
        self._request_seq += 1
        seq = self._request_seq
        reply.finished.connect(lambda: self._got_mesh(reply, identity, seq, location))

    def _got_mesh(self, reply, identity, seq, location):
        if not isValid(reply):
            return
        code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        raw = bytes(reply.readAll())
        reply.deleteLater()
        if not isValid(self):
            return
        if self._pending_reply is reply:
            self._pending_reply = None
        if seq != self._request_seq or identity != self._active_id:
            return
        meta = self.models.get(identity, {})
        if (code != 200 or not raw or len(raw) > MAX_ASSET_BYTES or
            hashlib.sha256(raw).hexdigest() != meta.get('sha256')):
            self.status.setText(self.t('invalid'))
            return
        try:
            location.parent.mkdir(parents=True, exist_ok=True)
            # Content already SHA-verified; don't execute external scripts.
            location.write_bytes(raw)
            self._render(location, identity)
        except OSError:
            self.status.setText(self.t('invalid'))

    def _render(self, path, identity):
        try:
            from .render3d.backend_policy import load_native_renderer
            pv, QtInteractor = load_native_renderer()
        except (ImportError, RuntimeError):
            # One canonical 3D adapter; a missing or mismatched Qt binding is
            # not evidence of a working GPU. Keep the source-verified 2D list.
            self.status.setText(self.t('install') + ' · 2D')
            self._show_2d_fallback()
            return
        try:
            mesh = pv.read(str(path))
            if getattr(mesh, 'n_points', 0) < 30 or getattr(mesh, 'n_cells', 0) < 30:
                raise ValueError('Empty/degenerate geometry')
            if self.viewer is None:
                self.viewer = QtInteractor(self)
                # Real viewer-scoped camera transforms; preserve native mouse.
                from .render3d.camera_controls import install_camera_shortcuts
                from .render3d.region_keyboard import install_region_keyboard
                install_camera_shortcuts(self.viewer)
                install_region_keyboard(self.viewer, self.selector)
                self.viewer.setMinimumHeight(340)
                self.content.addWidget(self.viewer, 1)
                self.empty.hide()
            if hasattr(self.viewer, 'disable_picking'):
                try:
                    self.viewer.disable_picking()
                except RuntimeError:
                    pass
            self.viewer.clear()
            self.viewer.add_mesh(mesh, name=identity, color='#ECCAA7',
                                 smooth_shading=True, specular=0.14, specular_power=20,
                                 pickable=True)
            try:
                self.viewer.enable_mesh_picking(callback=self.on_pick, show=False, show_message=False)
            except TypeError:
                self.viewer.enable_mesh_picking(callback=self.on_pick, show=False)
            self.viewer.reset_camera()
            if self.fallback_2d is not None:
                self.fallback_2d.hide()
            self.viewer.show()
            self.reset_button.setEnabled(True)
            self.status.setText(self.t('ready', name=self.selector.currentText(),
                                       n=mesh.n_points, cells=mesh.n_cells))
        except (OSError, ValueError, RuntimeError) as exc:
            self.status.setText(self.t('invalid') + f' ({type(exc).__name__})')
            # A failed native graphics/VTK environment must not strand the
            # user on a blank area. This is a clearly labelled 2D list only.
            if isinstance(exc, RuntimeError):
                self._show_2d_fallback()

    def _show_2d_fallback(self):
        # Import lazily: a working VTK viewport still uses exactly the
        # original renderer, while unsupported machines get a Qt-only list.
        if self.fallback_2d is None:
            from .render3d.accessibility_fallback import build_accessible_anatomy_2d
            self.fallback_2d = build_accessible_anatomy_2d(self, locale=self.locale)
            self.fallback_2d.structure_selected.connect(self._selected_from_2d)
            self.content.addWidget(self.fallback_2d, 1)
        else:
            self.fallback_2d.set_locale(self.locale)
        if self.viewer is not None:
            self.viewer.hide()
        self.empty.hide()
        self.fallback_2d.show()
        self.reset_button.setEnabled(False)

    def _selected_from_2d(self, identity):
        index = self.selector.findData(identity)
        if index < 0:
            return
        if self.selector.currentIndex() != index:
            self.selector.setCurrentIndex(index)
        self._active_id = identity
        # Explicitly label this as a 2D selection, not VTK mesh picking.
        self.status.setText(self.t('selected', name=self.selector.currentText()) + ' · 2D')

    def reset_camera(self):
        if self.viewer is not None:
            self.viewer.reset_camera()

    def on_pick(self, mesh):
        if mesh is not None and self._active_id:
            self.status.setText(self.t('selected', name=self.selector.currentText()))

    def show_source_inspector(self):
        from .render3d.source_inspector import (
            build_source_inspector_dialog, source_evidence,
        )
        try:
            evidence = source_evidence(
                self.models.get(self._active_id), approved_root=ASSETS
            )
        except ValueError:
            self.status.setText(self.t('invalid'))
            return
        dialog = build_source_inspector_dialog(evidence, self, locale=self.locale)
        dialog.exec()

    def open_source(self):
        meta = self.models.get(self._active_id, {})
        url = str(meta.get('source_url', ''))
        if url.startswith('https://'):
            QDesktopServices.openUrl(QUrl(url))

    def closeEvent(self, event):
        self._request_seq += 1
        if getattr(self, '_pending_reply', None) is not None and isValid(self._pending_reply):
            self._pending_reply.abort()
            self._pending_reply = None
        if self.viewer is not None:
            self.viewer.close()
        super().closeEvent(event)
