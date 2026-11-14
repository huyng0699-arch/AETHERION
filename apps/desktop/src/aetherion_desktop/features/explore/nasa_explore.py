"""Native five-hazard NASA Explore reference reader (Q-0117).

Reads only local, explicitly identified AETHERION JSON files. These references
are NOT live astronaut telemetry, diagnostic evidence, or verified treatment
advice. No network call occurs until the user deliberately opens a source URL.
"""
from __future__ import annotations

from dataclasses import dataclass
from html import escape
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

TOPICS: tuple[tuple[str, str, str], ...] = (
    ("space_radiation", "Space radiation", "space_radiation.json"),
    ("isolation_and_confinement", "Isolation and confinement", "isolation_confinement.json"),
    ("distance_from_earth", "Distance from Earth", "distance_from_earth.json"),
    ("gravity_fields", "Altered gravity", "altered_gravity.json"),
    ("hostile_closed_environments", "Hostile / closed habitat", "hostile_closed_environment.json"),
)

DETAIL_FIELDS: tuple[tuple[str, str], ...] = (
    ("affected_organ_systems", "Systems discussed in the research"),
    ("consequences", "Physiological research context"),
    ("observable_indicators_in_aetherion", "Candidate indicators — not live sensor readings"),
    ("behavioral_indicators_without_clinical_overclaim", "Wellbeing indicators and limits"),
    ("communication_delay_and_autonomy_constraints", "Communication and autonomy"),
    ("scope_separation", "Cabin measurements versus personal health"),
)

MAX_SOURCE_BYTES = 200_000


@dataclass(frozen=True)
class HazardReference:
    hazard_id: str
    title: str
    state: str
    sections: tuple[tuple[str, object], ...]
    sources: tuple[tuple[str, str], ...]
    limitations: tuple[str, ...]
    error: str = ""


def trusted_source_url(url: str) -> bool:
    """Only navigate HTTPS links on official source hosts, with no credentials."""
    try:
        u = urlsplit(url)
        host = (u.hostname or "").lower()
        return (u.scheme == "https"
                and u.username is None and u.password is None and u.port is None
                and (host == "nasa.gov" or host.endswith(".nasa.gov")
                     or host == "spaceappschallenge.org"
                     or host.endswith(".spaceappschallenge.org")))
    except ValueError:
        return False


def default_hazards_directory() -> Path:
    override = os.environ.get("AETHERION_NASA_HAZARDS_DIR")
    if override:
        return Path(override).expanduser()
    # During development this is under repository/knowledge. A packaged build
    # must explicitly bundle the JSON or set AETHERION_NASA_HAZARDS_DIR.
    source = Path(__file__).resolve()
    for ancestor in source.parents:
        candidate = ancestor / "knowledge" / "nasa" / "hazards"
        if candidate.is_dir():
            return candidate
    return source.parent / "not_installed"


def _read_reference(directory: Path, hazard_id: str, title: str, filename: str) -> HazardReference:
    target = directory / filename
    if not target.is_file():
        return HazardReference(hazard_id, title, "SOURCE_MISSING", (), (), (),
                               "Original reference JSON is not bundled on this installation")
    try:
        if target.stat().st_size > MAX_SOURCE_BYTES:
            raise ValueError("Source file is larger than supported local reference limit")
        source = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(source, dict):
            raise ValueError("Expected JSON object")
        if source.get("hazard_id") != hazard_id or source.get("schema_version") != "1.0.0":
            raise ValueError("Hazard ID / reference schema mismatch")
        if source.get("is_live_telemetry") is not False:
            raise ValueError("Historical science is incorrectly flagged as live data")
        sources = source.get("primary_sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError("Missing source attribution list")
        accepted: list[tuple[str, str]] = []
        for item in sources:
            if not isinstance(item, dict):
                raise ValueError("Invalid source item")
            url = str(item.get("url", ""))
            if not trusted_source_url(url):
                raise ValueError("Source URL is not an allowed official HTTPS destination")
            label = str(item.get("publisher") or item.get("source_id") or "NASA source").strip()
            accepted.append((label, url))
        fields = tuple((label, source[key]) for key, label in DETAIL_FIELDS if key in source)
        limits = source.get("limitations", [])
        if not isinstance(limits, list) or not all(isinstance(v, str) for v in limits):
            raise ValueError("Invalid reference limitations")
        return HazardReference(hazard_id, str(source.get("title") or title), "REFERENCE_ONLY",
                               fields, tuple(accepted), tuple(limits))
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        return HazardReference(hazard_id, title, "SOURCE_ERROR", (), (), (),
                               f"Reference cannot be safely displayed: {type(exc).__name__}")


def load_hazard_references(directory: str | Path | None = None) -> tuple[HazardReference, ...]:
    """Load exactly five locally installed topics, never create missing data."""
    root = Path(directory) if directory is not None else default_hazards_directory()
    return tuple(_read_reference(root, hazard_id, label, filename)
                 for hazard_id, label, filename in TOPICS)


def _render_value(value: object, depth: int = 0) -> str:
    """Escape source text and give nested reference structures legible headings."""
    if depth >= 5:
        return "<em>Further nested detail omitted; see original source file.</em>"
    if isinstance(value, str):
        return escape(value)
    if value is None:
        return "Not specified"
    if isinstance(value, (int, float, bool)):
        return escape(str(value))
    if isinstance(value, list):
        if not value:
            return "<em>Not documented in this source.</em>"
        return "<ul>" + "".join("<li>" + _render_value(v, depth + 1) + "</li>" for v in value) + "</ul>"
    if isinstance(value, dict):
        rows = []
        for key, child in value.items():
            if key in ("source_ids",):
                label = "Linked source IDs"
            else:
                label = str(key).replace("_", " ").capitalize()
            rows.append("<p><strong>" + escape(label) + ":</strong> " +
                        _render_value(child, depth + 1) + "</p>")
        return "".join(rows)
    return "<em>Unsupported reference field.</em>"


def render_hazard_html(item: HazardReference) -> str:
    """Build one safe, static Qt-rich-text document with source drilldowns."""
    title = escape(item.title)
    if item.state != "REFERENCE_ONLY":
        return (f"<h2>{title}</h2><p><strong>{escape(item.state)}</strong></p>"
                f"<p>{escape(item.error)}</p>"
                "<p>No data is interpreted as normal health; no measurements were inferred.</p>")
    parts = [
        f"<h2>{title}</h2>",
        "<p><strong>Research reference only.</strong> This is an offline source-linked "
        "education view, NOT live crew telemetry, dosimetry, diagnosis or medical guidance.</p>",
        "<p><strong>Observation status:</strong> NO_DATA — this reference view has no "
        "authorized sensor or subject observations to display.</p>",
    ]
    for label, value in item.sections:
        parts.append("<h3>" + escape(label) + "</h3>" + _render_value(value))
    parts.append("<h3>Scientific source links (internet needed when opening)</h3><ul>")
    for publisher, url in item.sources:
        safe = escape(url, quote=True)
        parts.append('<li><a href="' + safe + '">' + escape(publisher) + "</a> — "
                     + escape(url) + "</li>")
    parts.append("</ul><h3>Evidence limitations</h3>")
    parts.append(_render_value(list(item.limitations)))
    parts.append("<p><em>NASA research material is separate from AETHERION's "
                 "person-specific, authenticated observation store.</em></p>")
    return "".join(parts)


def build_nasa_explore_page(parent=None):
    """Return a genuine native QWidget, never a WebEngine wrapper."""
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import (
        QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton,
        QSplitter, QTextBrowser, QVBoxLayout, QWidget,
    )

    class NASAExplorePage(QWidget):
        def __init__(self):
            super().__init__(parent)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(18, 20, 18, 16)
            heading = QLabel("NASA Explore · Five spaceflight hazards")
            heading.setObjectName("heading")
            layout.addWidget(heading)
            self.status = QLabel("OFFLINE science references only; no measurements or medical verdicts.")
            self.status.setWordWrap(True)
            layout.addWidget(self.status)
            tools = QHBoxLayout()
            tools.addStretch(1)
            reload_button = QPushButton("Reload offline references")
            reload_button.clicked.connect(self.reload)
            tools.addWidget(reload_button)
            layout.addLayout(tools)

            split = QSplitter(Qt.Orientation.Horizontal)
            self.topics = QListWidget()
            self.topics.setAccessibleName("Choose one NASA spaceflight hazard")
            self.topics.setMinimumWidth(225)
            split.addWidget(self.topics)

            self.detail = QTextBrowser()
            self.detail.setAccessibleName("NASA hazard context, limitations and official sources")
            self.detail.setOpenExternalLinks(False)
            self.detail.anchorClicked.connect(self.open_source)
            split.addWidget(self.detail)
            split.setSizes([240, 780])
            layout.addWidget(split, 1)

            note = QLabel("Research evidence ≠ live astronaut sensor data. "
                          "Missing readings never imply health or unconsciousness.")
            note.setWordWrap(True)
            layout.addWidget(note)

            self.references: tuple[HazardReference, ...] = ()
            self.topics.currentRowChanged.connect(self.show_hazard)
            self.reload()

        def reload(self):
            selected = self.topics.currentRow()
            self.references = load_hazard_references()
            self.topics.clear()
            for reference in self.references:
                state = "" if reference.state == "REFERENCE_ONLY" else f" [{reference.state}]"
                self.topics.addItem(reference.title + state)
            missing = sum(ref.state != "REFERENCE_ONLY" for ref in self.references)
            self.status.setText(
                f"{len(self.references) - missing}/5 local NASA hazard reference files loaded. "
                "Source links require internet; observations are not loaded.")
            self.topics.setCurrentRow(selected if 0 <= selected < len(self.references) else 0)

        def show_hazard(self, index: int):
            if 0 <= index < len(self.references):
                self.detail.setHtml(render_hazard_html(self.references[index]))
            else:
                self.detail.setHtml("<p>No NASA hazard selected.</p>")

        def open_source(self, url):
            url_text = url.toString()
            if not trusted_source_url(url_text):
                QMessageBox.warning(self, "Source blocked",
                                    "Only official NASA and NASA Space Apps HTTPS source links may be opened.")
                return
            if not QDesktopServices.openUrl(url):
                QMessageBox.information(self, "Source unavailable",
                    "The source could not be opened. Local reference text remains accessible offline.")

    return NASAExplorePage()
