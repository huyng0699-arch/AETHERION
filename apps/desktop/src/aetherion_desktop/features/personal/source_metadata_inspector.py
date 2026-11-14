"""Native Personal Today provenance inspector for an explicitly selected record.

No device origin is inferred from heart rate, ECG or any other metric. A source
identifier is not itself evidence of a medical sensor or clinical verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

QUALITY = frozenset({'READY', 'NO_DATA', 'STALE', 'OFFLINE', 'DENIED', 'ERROR', 'UNVERIFIED'})


@dataclass(frozen=True)
class SourceDetail:
    metric: str
    recorded_reading: str
    source_id: str
    scope: str
    observed_at_utc: str
    quality: str
    verification_state: str
    device_identity: str
    device_evidence: str
    received_at_utc: str | None
    note: str


def _timestamp(text: object) -> str:
    if not isinstance(text, str):
        raise ValueError('timestamp missing')
    dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError('timestamp lacks time zone')
    return dt.astimezone(timezone.utc).isoformat()


def source_detail_from_card(card: object, *, selected_subject_id: str,
                            original: Mapping | None = None) -> SourceDetail:
    """Inspect authenticated card provenance without promoting unknown hardware.

    Optional original API record must match the exact selected person, metric,
    time, source and scope. The caller must already have authenticated it.
    """
    if not isinstance(selected_subject_id, str) or not selected_subject_id.strip():
        raise ValueError('explicit authorized subject is required')
    values = {key: getattr(card, key, None) for key in
              ('metric', 'reading', 'source_id', 'scope', 'observed_at',
               'quality', 'verification_state')}
    if any(not isinstance(val, str) or not val.strip() for val in values.values()):
        raise ValueError('card has incomplete provenance')
    if values['quality'] not in QUALITY:
        raise ValueError('unknown data quality')
    observed_utc = _timestamp(values['observed_at'])
    source = values['source_id']
    verification = values['verification_state']
    device = 'NOT PROVIDED'
    device_evidence = 'No verified physical device identity available'
    received = None
    if original is not None:
        if not isinstance(original, Mapping):
            raise ValueError('original record must be a mapping')
        for key in ('subject_id', 'metric', 'source_id', 'scope'):
            expected = selected_subject_id if key == 'subject_id' else values[key]
            if original.get(key) != expected:
                raise ValueError('original record identity/provenance mismatch')
        if _timestamp(original.get('observed_at')) != observed_utc:
            raise ValueError('original record observation time mismatch')
        received_raw = original.get('received_at')
        if received_raw is not None:
            received = _timestamp(received_raw)
            if datetime.fromisoformat(received) < datetime.fromisoformat(observed_utc):
                raise ValueError('record received before measurement')
        candidate = original.get('device_id')
        if candidate is not None:
            if not isinstance(candidate, str) or not candidate.strip():
                raise ValueError('invalid device identifier')
            device = candidate.strip()
            # A provided ID is not hardware attestation or automatic clinical verification.
            device_evidence = 'Reported device ID; physical device not independently attested'
    if verification != 'VERIFIED' or values['quality'] != 'READY':
        note = 'Source/quality is not fully verified; not a diagnosis or live sensor guarantee'
    else:
        note = 'Source quality reported READY; no clinical or hardware certification implied'
    return SourceDetail(values['metric'], values['reading'], source, values['scope'],
                        observed_utc, values['quality'], verification,
                        device, device_evidence, received, note)


def build_source_detail_dialog(detail: SourceDetail, parent=None):
    """Qt-native dialog with actual source, time, unit and device uncertainty."""
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLabel

    dialog = QDialog(parent)
    dialog.setWindowTitle('Measurement source & quality')
    dialog.setAccessibleName('Selected personal observation provenance')
    layout = QFormLayout(dialog)
    rows = (
        ('Measurement', detail.metric), ('Recorded value/unit', detail.recorded_reading),
        ('Original source ID', detail.source_id), ('Scope', detail.scope),
        ('Measured at (UTC)', detail.observed_at_utc), ('Received at (UTC)', detail.received_at_utc or 'NOT PROVIDED'),
        ('Data quality', detail.quality), ('Verification', detail.verification_state),
        ('Reported device', detail.device_identity), ('Device status', detail.device_evidence),
    )
    for label, value in rows:
        field = QLabel(str(value))
        field.setWordWrap(True)
        field.setTextInteractionFlags(field.textInteractionFlags() | Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addRow(label, field)
    warning = QLabel(detail.note)
    warning.setWordWrap(True)
    layout.addRow('Limitations', warning)
    close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    close.rejected.connect(dialog.reject)
    layout.addRow(close)
    return dialog
