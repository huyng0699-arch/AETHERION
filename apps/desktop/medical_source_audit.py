"""Native Qt source/safety audit panel for an offline medical-library article.

Caller supplies provenance from the verified local store; this panel never infers
NASA endorsement, clinical authority, rights clearance, or offline verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import QFormLayout, QGroupBox, QLabel, QVBoxLayout, QWidget


class SourceKind(str, Enum):
    NASA_CLIFF = "nasa_cliff"
    CLINICAL_PROTOCOL = "clinical_protocol"
    OTHER_REFERENCE = "other_reference"


@dataclass(frozen=True)
class ArticleAudit:
    title: str
    source_kind: SourceKind
    original_url: str | None = None
    source_version: str | None = None
    source_sha256: str | None = None
    original_verified: bool = False
    offline_bytes_verified: bool = False
    full_text_verified: bool = False
    page_citations_verified: bool = False
    images_total: int = 0
    images_with_verified_rights: int = 0
    curated_images: int = 0

    def __post_init__(self) -> None:
        if min(self.images_total, self.images_with_verified_rights, self.curated_images) < 0:
            raise ValueError("Image counts must be nonnegative")
        if self.images_with_verified_rights > self.images_total or self.curated_images > self.images_total:
            raise ValueError("Image counts exceed total")


def audit_lines(audit: ArticleAudit) -> tuple[tuple[str, str], ...]:
    """Fail closed: provenance flags are evidence supplied by the caller, not verified here."""
    kind = {
        SourceKind.NASA_CLIFF: "NASA CliFF risk-planning reference — NOT a bedside clinical protocol",
        SourceKind.CLINICAL_PROTOCOL: "Clinical protocol claim — requires separate clinical validation",
        SourceKind.OTHER_REFERENCE: "Reference material — clinical authority not established",
    }[audit.source_kind]
    original = bool(audit.original_verified and audit.original_url and audit.source_version and audit.source_sha256)
    offline = bool(original and audit.offline_bytes_verified)
    completeness = bool(offline and audit.full_text_verified and audit.page_citations_verified)
    return (
        ("Material classification", kind),
        ("NASA endorsement", "NOT endorsed or clinically certified by NASA"),
        ("Original provenance", "Verified by upstream source audit" if original else "UNVERIFIED — original URL/version/SHA or validation missing"),
        ("Offline original", "Verified by upstream offline byte audit" if offline else "UNVERIFIED — do not claim original is available offline"),
        ("Article completeness", "Full text and page citations checked upstream" if completeness else "INCOMPLETE / UNVERIFIED"),
        ("Original URL", audit.original_url or "Not provided"),
        ("Version", audit.source_version or "Not provided"),
        ("Source SHA-256", audit.source_sha256 or "Not provided"),
        ("Images", f"{audit.images_with_verified_rights}/{audit.images_total} with upstream rights verification; {audit.curated_images} author-curated (not NASA originals)"),
        ("Safety", "Reference only. Not individualized diagnosis, treatment or emergency guidance."),
    )


class MedicalSourceAuditPanel(QWidget):
    """Embeddable native widget; no network access or patient-data processing."""

    def __init__(self, audit: ArticleAudit | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        group = QGroupBox("Medical source audit and safety", self)
        self._form = QFormLayout(group)
        self._labels: list[QLabel] = []
        layout.addWidget(group)
        layout.addStretch(1)
        self.set_audit(audit)

    def set_audit(self, audit: ArticleAudit | None) -> None:
        while self._form.rowCount():
            self._form.removeRow(0)
        self._labels.clear()
        if audit is None:
            rows = (("Status", "NO DATA — no verified offline article selected"),)
        else:
            rows = audit_lines(audit)
        for key, value in rows:
            label = QLabel(value, self)
            label.setWordWrap(True)
            label.setTextInteractionFlags(label.textInteractionFlags())
            label.setAccessibleName(key)
            self._form.addRow(key + ":", label)
            self._labels.append(label)
