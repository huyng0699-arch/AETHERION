"""Authenticated ECG waveforms: actual device/import samples only, never synthesized.

The same canonical SQLite database, subject ACL, and bearer sessions are used.
A passing checksum means file integrity, not device authenticity or diagnosis.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
import sqlite3
import struct
import uuid
import zlib
from typing import Callable, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, field_validator, model_validator

from ..security import is_subject_authorized
from ..store import get_subject

MAX_SAMPLES = 100_000
MAX_SECONDS = 120.0
MAX_BLOB_BYTES = MAX_SAMPLES * 4
ECG_LEADS = frozenset({'I','II','III','aVR','aVL','aVF',*(f'V{i}' for i in range(1,7)),'single'})


class ECGUpload(BaseModel):
    subject_id: str = Field(min_length=1, max_length=80)
    source_id: str = Field(min_length=3, max_length=120)
    recorded_at: datetime
    sample_rate_hz: float = Field(ge=50, le=2000)
    lead_name: str = Field(min_length=1, max_length=8)
    samples_millivolts: list[float] = Field(min_length=250, max_length=MAX_SAMPLES)
    original_source_sha256: str | None = Field(default=None, pattern=r'^[0-9a-fA-F]{64}$')
    sample_origin: Literal['DEVICE_IMPORT','RESEARCH_IMPORT']
    attested_real_signal: bool = False

    @field_validator('recorded_at')
    @classmethod
    def require_timezone(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Recorded time must have timezone offset')
        return value

    @field_validator('lead_name')
    @classmethod
    def valid_lead(cls, value):
        if value not in ECG_LEADS:
            raise ValueError('Unsupported ECG lead')
        return value

    @field_validator('samples_millivolts')
    @classmethod
    def valid_voltages(cls, values):
        if any(not math.isfinite(v) or abs(v) > 50 for v in values):
            raise ValueError('Sample must be finite and within 50 mV import bounds')
        return values

    @model_validator(mode='after')
    def ensure_actual_signal(self):
        if self.attested_real_signal is not True:
            raise ValueError('Explicit attestation of original, real recorded samples is required')
        if len(self.samples_millivolts) / self.sample_rate_hz > MAX_SECONDS:
            raise ValueError('Import exceeds 120-second recording limit')
        if self.recorded_at.astimezone(timezone.utc) > datetime.now(timezone.utc):
            raise ValueError('Recording time may not be in the future')
        return self


def _connect(db: Path | str):
    conn = sqlite3.connect(db, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def ensure_schema(db: Path | str) -> None:
    with _connect(db) as conn:
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS ecg_recordings (
                recording_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL,
                created_by TEXT NOT NULL,
                source_id TEXT NOT NULL,
                lead_name TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                sample_rate_hz REAL NOT NULL,
                sample_count INTEGER NOT NULL,
                duration_seconds REAL NOT NULL,
                sample_origin TEXT NOT NULL,
                verification_state TEXT NOT NULL CHECK(verification_state = 'UNVERIFIED'),
                waveform_sha256 TEXT NOT NULL,
                original_source_sha256 TEXT,
                samples_zlib BLOB NOT NULL,
                imported_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_ecg_subject_recorded
            ON ecg_recordings(subject_id,recorded_at DESC);
        ''')


def _metadata(row: sqlite3.Row) -> dict:
    return {name: row[name] for name in (
        'recording_id','subject_id','source_id','lead_name','recorded_at',
        'sample_rate_hz','sample_count','duration_seconds','sample_origin',
        'verification_state','waveform_sha256','original_source_sha256','imported_at'
    )} | {'unit':'mV','clinical_interpretation':'NOT_PERFORMED',
         'sample_source_verified':False,'contains_real_attested_signal':True}


def _decimate(samples: tuple[float, ...], max_points: int) -> list[dict]:
    """Min/max decimation retains peaks and chronological order; no invented points."""
    n = len(samples)
    indices = []
    if n <= max_points:
        indices = list(range(n))
    else:
        bucket_size = math.ceil(n / max(1, max_points // 2))
        for start in range(0, n, bucket_size):
            stop = min(n, start + bucket_size)
            imin = min(range(start, stop), key=samples.__getitem__)
            imax = max(range(start, stop), key=samples.__getitem__)
            indices.extend(sorted(set((imin, imax))))
        if len(indices) > max_points:
            indices = indices[:max_points]
    return [{'index':i,'millivolts':float(samples[i])} for i in indices]


def build_ecg_router(db_path: Callable[[], Path], require_session: Callable) -> APIRouter:
    router = APIRouter(prefix='/api/v1/ecg', tags=['ECG source-backed waveforms'])

    def require_subject(session: dict, subject_id: str) -> None:
        if not is_subject_authorized(session['role'], session['allowed_subjects'], subject_id):
            raise HTTPException(status_code=403, detail='Subject access denied')
        if get_subject(db_path(), subject_id) is None:
            raise HTTPException(status_code=404, detail='Subject not found')

    @router.post('/recordings', status_code=201)
    def upload(item: ECGUpload, identity: tuple[dict, str] = Depends(require_session)):
        session, _ = identity
        require_subject(session, item.subject_id)
        ensure_schema(db_path())
        samples = struct.pack('<' + str(len(item.samples_millivolts)) + 'f', *item.samples_millivolts)
        digest = hashlib.sha256(samples).hexdigest()
        record_id = 'ecg-' + uuid.uuid4().hex[:20]
        now = datetime.now(timezone.utc).isoformat()
        values = (record_id, item.subject_id, session['username'], item.source_id,
                  item.lead_name, item.recorded_at.astimezone(timezone.utc).isoformat(),
                  item.sample_rate_hz, len(item.samples_millivolts),
                  len(item.samples_millivolts)/item.sample_rate_hz, item.sample_origin,
                  'UNVERIFIED', digest, item.original_source_sha256,
                  zlib.compress(samples, level=6), now)
        with _connect(db_path()) as conn:
            conn.execute('''INSERT INTO ecg_recordings(
                recording_id,subject_id,created_by,source_id,lead_name,recorded_at,
                sample_rate_hz,sample_count,duration_seconds,sample_origin,verification_state,
                waveform_sha256,original_source_sha256,samples_zlib,imported_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', values)
            conn.commit()
            row = conn.execute('SELECT * FROM ecg_recordings WHERE recording_id=?', (record_id,)).fetchone()
        return {'recording':_metadata(row),'notice':'Source attested by uploader, NOT independently device-verified; no medical interpretation.'}

    @router.get('/recordings')
    def list_recordings(subject_id: str = Query(min_length=1,max_length=80),
                        limit: int = Query(default=30,ge=1,le=100),
                        identity: tuple[dict, str] = Depends(require_session)):
        session, _ = identity
        require_subject(session, subject_id)
        ensure_schema(db_path())
        with _connect(db_path()) as conn:
            rows = conn.execute('SELECT * FROM ecg_recordings WHERE subject_id=? '
                                'ORDER BY recorded_at DESC LIMIT ?', (subject_id,limit)).fetchall()
        return {'subject_id':subject_id,'recordings':[_metadata(r) for r in rows],
                'clinical_interpretation':'NOT_PERFORMED'}

    @router.get('/recordings/{recording_id}')
    def read_recording(recording_id: str,
                       subject_id: str = Query(min_length=1,max_length=80),
                       max_points: int = Query(default=2400,ge=100,le=5000),
                       identity: tuple[dict, str] = Depends(require_session)):
        session, _ = identity
        require_subject(session, subject_id)
        ensure_schema(db_path())
        with _connect(db_path()) as conn:
            row = conn.execute('SELECT * FROM ecg_recordings WHERE recording_id=? AND subject_id=?',
                               (recording_id,subject_id)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail='Recording unavailable')
        try:
            decompressor = zlib.decompressobj()
            packed = decompressor.decompress(row['samples_zlib'], MAX_BLOB_BYTES + 1)
            if (not decompressor.eof or decompressor.unconsumed_tail or
                decompressor.unused_data or len(packed) > MAX_BLOB_BYTES):
                raise ValueError('Corrupted or oversized waveform')
        except (zlib.error, ValueError):
            raise HTTPException(status_code=409, detail='Corrupted ECG data')
        if len(packed) != 4*row['sample_count'] or hashlib.sha256(packed).hexdigest() != row['waveform_sha256']:
            raise HTTPException(status_code=409, detail='ECG integrity check failed')
        samples = struct.unpack('<' + str(row['sample_count']) + 'f',packed)
        points = _decimate(samples,max_points)
        return {'recording':_metadata(row),'points':points,'display_decimated':len(points)<len(samples),
                'clinical_interpretation':'NOT_PERFORMED',
                'notice':'Display data only. Neither diagnostic waveform review nor device authenticity certified.'}

    return router
