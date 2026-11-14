"""Single AETHERION native 3D renderer contract.

PyVistaQt/VTK is the sole implemented 3D renderer. Unsupported environments
fall back to the explicitly labelled, non-3D Qt list (Q-0131), never to an
unverified VisPy/web placeholder. Windows performance and license acceptance
are separate release gates; import success alone is NOT GPU evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from pathlib import Path
from typing import Any

CANONICAL_BACKEND = "pyvistaqt"
REQUIRED_DISTRIBUTIONS = ("PySide6", "pyvista", "pyvistaqt", "vtk")


@dataclass(frozen=True)
class DistributionEvidence:
    name: str
    version: str | None
    license_from_metadata: str | None
    native_library_count: int
    native_library_bytes: int
    checked_files: int


@dataclass(frozen=True)
class RendererAudit:
    backend: str
    installed: bool
    packages: tuple[DistributionEvidence, ...]
    platform: str
    measured_fps: float | None = None
    measured_picking_ms: float | None = None
    dll_audit_complete: bool = False

    @property
    def needs_native_acceptance(self) -> bool:
        return True  # A metadata audit never certifies real GPU, Windows or picking.


def _native_filename(name: str) -> bool:
    text = name.lower()
    return text.endswith((".dll", ".pyd", ".dylib", ".so")) or ".so." in text


def inspect_installed_renderer() -> RendererAudit:
    """Record real installed metadata/linked-library footprint, not estimates.

    Only invoke in a controlled QA environment: package metadata can include
    thousands of files. Missing dist, unreadable file or unverified licensing
    are represented as missing/partial evidence, never invented PASS.
    """
    import platform

    collected = []
    for name in REQUIRED_DISTRIBUTIONS:
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            collected.append(DistributionEvidence(name, None, None, 0, 0, 0))
            continue
        m = dist.metadata
        license_text = m.get("License-Expression") or m.get("License")
        if not license_text:
            license_text = None  # Requires independent legal audit.
        count, byte_count, checked = 0, 0, 0
        for item in dist.files or ():
            if not _native_filename(str(item)):
                continue
            try:
                file = Path(dist.locate_file(item))
                size = file.stat().st_size
            except (OSError, ValueError):
                continue
            if size >= 0:
                count += 1
                byte_count += size
                checked += 1
        collected.append(
            DistributionEvidence(name, dist.version, license_text,
                                 count, byte_count, checked)
        )
    return RendererAudit(
        backend=CANONICAL_BACKEND,
        installed=all(item.version is not None for item in collected),
        packages=tuple(collected),
        platform=platform.platform(),
    )


def load_native_renderer() -> tuple[Any, Any]:
    """Load the single actual PyVistaQt/VTK backend, or raise for 2D fallback.

    No fallback or dummy 3D implementation is imported here. The caller owns
    the real mesh/QtInteractor lifecycle; this only prevents renderer drift.
    """
    import pyvista as pv
    from pyvistaqt import QtInteractor

    # QtPy may select PyQt/PySide independently of this application's PySide6
    # shell. Mixing bindings in one process is unsafe.
    from qtpy import API_NAME
    if API_NAME.lower() != "pyside6":
        raise RuntimeError("AETHERION native Atlas requires PySide6 Qt binding")
    return pv, QtInteractor
