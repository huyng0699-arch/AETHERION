"""Authenticated Safety Incidents, Device Heartbeat, and Cross-Client Sync API (Q-0055, Q-0056, Q-0057, Q-0059)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Callable, Literal
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from .security import is_subject_authorized
from .signal_state import classify_technical_source_state


class IncidentReportIn(BaseModel):
    subject_id: str = Field(min_length=1, max_length=80)
    incident_type: Literal["WITNESS_REPORTED_UNCONSCIOUS", "UNANSWERED_CHECKIN", "NEED_HELP_NOW", "INJURY_REPORT"]
    witness_id: str | None = Field(default=None, max_length=80)
    note: str = Field(default="", max_length=500)
    source: str = Field(default="crew_report", min_length=1, max_length=120)


class IncidentAckIn(BaseModel):
    note: str = Field(default="", max_length=500)


class DeviceHeartbeatIn(BaseModel):
    source_id: str = Field(min_length=1, max_length=120)
    subject_id: str = Field(min_length=1, max_length=80)
    link_connected: bool = True
    sensor_error: bool = False
    last_observed_at: datetime | None = None


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS safety_incidents (
            incident_id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            incident_type TEXT NOT NULL,
            witness_id TEXT,
            source TEXT NOT NULL,
            note TEXT NOT NULL,
            status TEXT NOT NULL,
            unconsciousness_assumed INTEGER NOT NULL DEFAULT 0,
            acknowledged_by TEXT,
            acknowledged_at_utc TEXT,
            created_at_utc TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS device_heartbeats (
            source_id TEXT PRIMARY KEY,
            subject_id TEXT NOT NULL,
            link_connected INTEGER NOT NULL,
            sensor_error INTEGER NOT NULL,
            last_observed_at_utc TEXT,
            updated_at_utc TEXT NOT NULL
        );
        """
    )


def build_safety_router(
    db_path: Callable[[], Path],
    require_session: Callable,
    *,
    server_version: str = "0.2.0",
) -> APIRouter:
    router = APIRouter(tags=["Safety and Sync"])

    @router.post("/api/v1/safety/incidents", status_code=201)
    def report_incident(
        item: IncidentReportIn,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        sid = item.subject_id.strip()
        if not is_subject_authorized(session["role"], session["allowed_subjects"], sid):
            raise HTTPException(status_code=403, detail=f"Not authorized for subject '{sid}'")

        witness = (item.witness_id or "").strip() or None
        if item.incident_type == "WITNESS_REPORTED_UNCONSCIOUS" and not witness:
            raise HTTPException(
                status_code=422,
                detail="witness_id is required when reporting WITNESS_REPORTED_UNCONSCIOUS",
            )

        now_utc = datetime.now(timezone.utc).isoformat()
        incident_id = f"inc-{uuid.uuid4().hex[:12]}"
        with sqlite3.connect(db_path()) as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO safety_incidents (
                    incident_id, subject_id, incident_type, witness_id, source, note,
                    status, unconsciousness_assumed, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', 0, ?)
                """,
                (incident_id, sid, item.incident_type, witness, item.source.strip(), item.note.strip(), now_utc),
            )
            conn.commit()

        return {
            "incident_id": incident_id,
            "subject_id": sid,
            "incident_type": item.incident_type,
            "witness_id": witness,
            "status": "OPEN",
            "unconsciousness_assumed": False,
            "requires_human_or_witness_verification": item.incident_type == "UNANSWERED_CHECKIN",
            "created_at_utc": now_utc,
        }

    @router.post("/api/v1/safety/incidents/{incident_id}/ack")
    def acknowledge_incident(
        incident_id: str,
        _item: IncidentAckIn,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            row = conn.execute(
                "SELECT * FROM safety_incidents WHERE incident_id = ?",
                (incident_id,),
            ).fetchone()
            if row is None or not is_subject_authorized(session["role"], session["allowed_subjects"], row["subject_id"]):
                raise HTTPException(status_code=404, detail="Incident unavailable")

            already_acked = row["status"] == "ACKNOWLEDGED"
            ack_at = row["acknowledged_at_utc"] or datetime.now(timezone.utc).isoformat()
            ack_by = row["acknowledged_by"] or session["username"]
            if not already_acked:
                conn.execute(
                    """
                    UPDATE safety_incidents
                    SET status = 'ACKNOWLEDGED', acknowledged_by = ?, acknowledged_at_utc = ?
                    WHERE incident_id = ?
                    """,
                    (ack_by, ack_at, incident_id),
                )
                conn.commit()

        return {
            "incident_id": incident_id,
            "subject_id": row["subject_id"],
            "status": "ACKNOWLEDGED",
            "acknowledged_by": ack_by,
            "acknowledged_at_utc": ack_at,
            "idempotent_replay": already_acked,
        }

    @router.post("/api/v1/devices/heartbeat")
    def record_device_heartbeat(
        item: DeviceHeartbeatIn,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        sid = item.subject_id.strip()
        if not is_subject_authorized(session["role"], session["allowed_subjects"], sid):
            raise HTTPException(status_code=403, detail=f"Not authorized for subject '{sid}'")

        now_utc = datetime.now(timezone.utc).isoformat()
        last_obs = item.last_observed_at.astimezone(timezone.utc).isoformat() if item.last_observed_at else None
        with sqlite3.connect(db_path()) as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO device_heartbeats (
                    source_id, subject_id, link_connected, sensor_error, last_observed_at_utc, updated_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    subject_id=excluded.subject_id,
                    link_connected=excluded.link_connected,
                    sensor_error=excluded.sensor_error,
                    last_observed_at_utc=excluded.last_observed_at_utc,
                    updated_at_utc=excluded.updated_at_utc
                """,
                (item.source_id.strip(), sid, int(item.link_connected), int(item.sensor_error), last_obs, now_utc),
            )
            conn.commit()
        return {"source_id": item.source_id.strip(), "subject_id": sid, "updated_at_utc": now_utc}

    @router.get("/api/v1/devices/{source_id}/status")
    def device_heartbeat_status(
        source_id: str,
        stale_after_seconds: float = Query(300.0, ge=1.0, le=86400.0),
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            row = conn.execute(
                "SELECT * FROM device_heartbeats WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        if row is None:
            return {
                "source_id": source_id,
                "signal_state": "NO_DATA",
                "connected": False,
                "last_seen_at_utc": None,
                "medical_emergency": False,
            }
        if not is_subject_authorized(session["role"], session["allowed_subjects"], row["subject_id"]):
            raise HTTPException(status_code=403, detail=f"Not authorized for device '{source_id}'")

        tech = classify_technical_source_state(
            source_id=source_id,
            subject_id=row["subject_id"],
            link_connected=bool(row["link_connected"]),
            sensor_error=bool(row["sensor_error"]),
            last_observed_at=row["last_observed_at_utc"],
            stale_after_seconds=stale_after_seconds,
        )
        return {
            "source_id": source_id,
            "subject_id": row["subject_id"],
            "signal_state": tech.technical_state,
            "connected": bool(row["link_connected"]),
            "last_seen_at_utc": row["last_observed_at_utc"],
            "age_seconds": tech.age_seconds,
            "medical_emergency": False,
        }

    @router.get("/api/v1/sync/status")
    def sync_status(
        subject_id: str = Query(min_length=1, max_length=80),
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        sid = subject_id.strip()
        if not is_subject_authorized(session["role"], session["allowed_subjects"], sid):
            raise HTTPException(status_code=403, detail=f"Not authorized for subject '{sid}'")

        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            rows = conn.execute(
                "SELECT incident_id, status FROM safety_incidents WHERE subject_id = ? ORDER BY created_at_utc ASC",
                (sid,),
            ).fetchall()
        total = len(rows)
        acked = sum(1 for r in rows if r["status"] == "ACKNOWLEDGED")
        pending_ids = [r["incident_id"] for r in rows if r["status"] != "ACKNOWLEDGED"]
        return {
            "server_version": server_version,
            "subject_id": sid,
            "server_time_utc": datetime.now(timezone.utc).isoformat(),
            "incidents_total": total,
            "incidents_acknowledged": acked,
            "pending_ack_incident_ids": pending_ids,
        }

    return router
