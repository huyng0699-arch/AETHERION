"""Native 3D anatomy using existing PyVistaQt/VTK, never synthetic body meshes.

The server owns the approved anatomy asset catalogue; desktop renders on GPU.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

ROOT = Path(__file__).resolve().parents[4]
MANIFEST = ROOT / "knowledge/anatomy/approved_models.json"
ASSETS = ROOT / "knowledge/anatomy/meshes"
SUPPORTED = {".vtk", ".vtp", ".vtu", ".stl", ".obj", ".ply"}


def approved_models() -> list[dict]:
    if not MANIFEST.is_file():
        return []
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    root = ASSETS.resolve()
    models = []
    for item in manifest.get("models", []):
        if not isinstance(item, dict) or item.get("rights_status") != "APPROVED":
            continue
        filename, digest = item.get("filename"), item.get("sha256")
        if not isinstance(filename, str) or not isinstance(digest, str) or len(digest) != 64:
            continue
        mesh = (root / filename).resolve()
        if not mesh.is_relative_to(root) or not mesh.is_file() or mesh.suffix.lower() not in SUPPORTED:
            continue
        if hashlib.sha256(mesh.read_bytes()).hexdigest() != digest.lower():
            continue
        models.append({**item, "resolved_path": str(mesh)})
    return models


class BodyAtlas3D(QWidget):
    """Real QtInteractor only if a rights-cleared anatomical model is installed."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.viewer = None
        models = approved_models()
        if not models:
            self.status.setText(
                "Chưa có mô hình giải phẫu được duyệt nguồn và SHA. "
                "Không thay bằng khối cầu hoặc ảnh 2D giả làm giải phẫu 3D."
            )
            return
        try:
            import pyvista as pv
            from pyvistaqt import QtInteractor
        except ImportError:
            self.status.setText(
                "Thiếu PyVistaQt/VTK. Cài tùy chọn 'aetherion-desktop[atlas]'."
            )
            return
        self.viewer = QtInteractor(self)
        layout.addWidget(self.viewer, 1)
        count = 0
        for model in models:
            mesh = pv.read(model["resolved_path"])
            if getattr(mesh, "n_points", 0) < 1:
                continue
            self.viewer.add_mesh(
                mesh, name=model.get("anatomical_id", model["filename"]),
                color=model.get("color", "#b5becd"), pickable=True,
            )
            count += 1
        if not count:
            self.status.setText("Không có mesh hợp lệ trong nguồn đã phê duyệt.")
            return
        self.viewer.enable_mesh_picking(callback=self.on_pick, show=False)
        self.viewer.reset_camera()
        self.status.setText(f"{count} mô hình 3D thật. Kéo để xoay, cuộn để thu phóng.")

    def on_pick(self, mesh):
        if mesh is not None:
            self.status.setText(
                f"Đã chọn vùng hình học gồm {mesh.n_points} điểm. "
                "Chưa xác thực ánh xạ tới cấu trúc giải phẫu."
            )

    def closeEvent(self, event):
        if self.viewer is not None:
            self.viewer.close()
        super().closeEvent(event)
