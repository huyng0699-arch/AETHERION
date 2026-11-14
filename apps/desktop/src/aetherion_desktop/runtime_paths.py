"""Runtime lookup for optional, read-only NASA scientific reference assets.

AETHERION Desktop is a client, not the server. No patient data, secret, model
weight or arbitrary relative file is bundled by these helpers.

PyInstaller --onedir layout (both formats are supported):
    AETHERION-Desktop.exe
    data/knowledge/nasa/cliff_119_2023/AETHERION_NASA_CLIFF_119.sqlite
    _internal/knowledge/nasa/hazards/*.json

The source checkout layout is repository_root/knowledge/nasa/...
"""
from __future__ import annotations

import os
from pathlib import Path
import sys


def _roots() -> tuple[Path, ...]:
    """Trusted candidate roots; never silently read an unrelated CWD."""
    roots: list[Path] = []
    if getattr(sys, "frozen", False):
        # Customer-visible sidecar assets take precedence over frozen bundles;
        # a missing SQLite library is never silently fabricated.
        roots.append(Path(sys.executable).resolve().parent / "data")
    internal = getattr(sys, "_MEIPASS", None)
    if isinstance(internal, str) and internal:
        roots.append(Path(internal).resolve())
    # Editable source checkout or an installed package that lives in a repo.
    source = Path(__file__).resolve()
    for parent in source.parents:
        if (parent / "knowledge" / "nasa").is_dir():
            roots.append(parent)
            break
    # Deduplicate without breaking precedence.
    return tuple(dict.fromkeys(roots))


def reference_path(*segments: str) -> Path:
    """Find an installed knowledge-relative path without network or fallback data.

    `segments` are fixed trusted package constants (not user-supplied URLs
    or arbitrary path fragments). Return the expected path even if missing so
    callers can report NO_DATA instead of manufacturing scientific content.
    """
    relative = Path("knowledge", *segments)
    if relative.is_absolute() or any(part in (".", "..") for part in relative.parts):
        raise ValueError("Scientific reference path must be package-relative")
    for root in _roots():
        candidate = root / relative
        if candidate.exists():
            return candidate
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data" / relative
    return Path(__file__).resolve().parent / "not_installed" / relative


def cliff_library_path() -> Path:
    """One unambiguous offline medical DB for both the index and article reader."""
    override = os.environ.get("AETHERION_CLIFF_LIBRARY_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    return reference_path(
        "nasa", "cliff_119_2023", "AETHERION_NASA_CLIFF_119.sqlite"
    )


def nasa_hazards_path() -> Path:
    """Locally installed original NASA topic JSON only, no external download."""
    override = os.environ.get("AETHERION_NASA_HAZARDS_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return reference_path("nasa", "hazards")
