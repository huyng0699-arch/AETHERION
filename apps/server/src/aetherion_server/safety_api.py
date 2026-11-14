"""Authenticated Safety Incidents, Device Heartbeat, and Cross-Client Sync API (Q-0055..Q-0059, Q-0173, Q-0175, Q-0176)."""

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

SENSITIVE_DETAIL_ROLES = frozenset({"crew", "flight_surgeon", "admin"})
AUDIT_VIEW_ROLES = frozenset({"flight_surgeon", "admin"})


class IncidentReportIn(BaseModel):
    subject_id: str = Field(min_length=1, max_length=80)
    incident_type: Literal["WITNESS_REPORTED_UNCONSCIOUS", "UNANSWERED_CHECKIN", "NEED_HELP_NOW", "INJURY_REPORT"]
    witness_id: str | None = Field(default=None, max_length=80)
    note: str = Field(default="", max_length=500)
    source: str = Field(default="crew_report", min_length=1, max_length=120)


class IncidentAckIn(BaseModel):
    note: str = Field(default="", max_length=500)


class NotificationDeliveryIn(BaseModel):
    channel: str = Field(min_length=1, max_length=64)
    transport_evidence_id: str = Field(min_length=1, max_length=128)


class TimeoutEvalIn(BaseModel):
    timeout_seconds: float = Field(default=300.0, ge=1.0, le=86400.0)
    now_utc: datetime | None = None


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
            escalation_state TEXT NOT NULL DEFAULT 'NONE',
            escalated_at_utc TEXT,
            created_at_utc TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS safety_incident_audit (
            audit_id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            actor_username TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            access_granted INTEGER NOT NULL,
            redacted INTEGER NOT NULL,
            accessed_at_utc TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS safety_notification_receipts (
            receipt_id TEXT PRIMARY KEY,
            incident_id TEXT NOT NULL,
            channel TEXT NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('PENDING', 'DELIVERED', 'ACKNOWLEDGED')),
            transport_evidence_id TEXT,
            delivered_at_utc TEXT,
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
    cols = {r[1] for r in conn.execute("PRAGMA table_info(safety_incidents)").fetchall()}
    if "escalation_state" not in cols:
        conn.execute("ALTER TABLE safety_incidents ADD COLUMN escalation_state TEXT NOT NULL DEFAULT 'NONE'")
    if "escalated_at_utc" not in cols:
        conn.execute("ALTER TABLE safety_incidents ADD COLUMN escalated_at_utc TEXT")


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
        receipt_id = f"rcpt-{uuid.uuid4().hex[:12]}"
        with sqlite3.connect(db_path()) as conn:
            _ensure_tables(conn)
            conn.execute(
                """
                INSERT INTO safety_incidents (
                    incident_id, subject_id, incident_type, witness_id, source, note,
                    status, unconsciousness_assumed, escalation_state, created_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN', 0, 'NONE', ?)
                """,
                (incident_id, sid, item.incident_type, witness, item.source.strip(), item.note.strip(), now_utc),
            )
            conn.execute(
                """
                INSERT INTO safety_notification_receipts (
                    receipt_id, incident_id, channel, state, transport_evidence_id,
                    delivered_at_utc, acknowledged_at_utc, created_at_utc
                ) VALUES (?, ?, 'onboard_bus', 'PENDING', NULL, NULL, NULL, ?)
                """,
                (receipt_id, incident_id, now_utc),
            )
            conn.commit()

        return {
            "incident_id": incident_id,
            "subject_id": sid,
            "incident_type": item.incident_type,
            "witness_id": witness,
            "status": "OPEN",
            "escalation_state": "NONE",
            "receipt_state": "PENDING",
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
                conn.execute(
                    """
                    UPDATE safety_notification_receipts
                    SET state = 'ACKNOWLEDGED', acknowledged_at_utc = ?
                    WHERE incident_id = ?
                    """,
                    (ack_at, incident_id),
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

    @router.get("/api/v1/safety/incidents/{incident_id}")
    def get_incident_details(
        incident_id: str,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        now_utc = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            row = conn.execute(
                "SELECT * FROM safety_incidents WHERE incident_id = ?",
                (incident_id,),
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Incident unavailable")

            authorized = is_subject_authorized(session["role"], session["allowed_subjects"], row["subject_id"])
            redacted = session["role"] not in SENSITIVE_DETAIL_ROLES
            conn.execute(
                """
                INSERT INTO safety_incident_audit (
                    audit_id, incident_id, actor_username, actor_role, access_granted, redacted, accessed_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"aud-{uuid.uuid4().hex[:12]}",
                    incident_id,
                    session["username"],
                    session["role"],
                    int(authorized),
                    int(redacted),
                    now_utc,
                ),
            )
            conn.commit()
            if not authorized:
                raise HTTPException(status_code=403, detail=f"Not authorized for subject '{row['subject_id']}'")

        return {
            "incident_id": row["incident_id"],
            "subject_id": row["subject_id"],
            "incident_type": row["incident_type"],
            "source": row["source"],
            "status": row["status"],
            "escalation_state": row["escalation_state"],
            "escalated_at_utc": row["escalated_at_utc"],
            "unconsciousness_assumed": bool(row["unconsciousness_assumed"]),
            "witness_id": None if redacted else row["witness_id"],
            "note": "[REDACTED_FOR_ROLE]" if redacted else row["note"],
            "redacted": redacted,
            "acknowledged_by": row["acknowledged_by"],
            "acknowledged_at_utc": row["acknowledged_at_utc"],
            "created_at_utc": row["created_at_utc"],
        }

    @router.get("/api/v1/safety/incidents/{incident_id}/audit")
    def get_incident_audit(
        incident_id: str,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        if session["role"] not in AUDIT_VIEW_ROLES:
            raise HTTPException(status_code=403, detail="Audit log requires flight_surgeon or admin role")
        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            rows = conn.execute(
                "SELECT * FROM safety_incident_audit WHERE incident_id = ? ORDER BY accessed_at_utc ASC",
                (incident_id,),
            ).fetchall()
        return {
            "incident_id": incident_id,
            "items": [
                {
                    "audit_id": r["audit_id"],
                    "actor_username": r["actor_username"],
                    "actor_role": r["actor_role"],
                    "access_granted": bool(r["access_granted"]),
                    "redacted": bool(r["redacted"]),
                    "accessed_at_utc": r["accessed_at_utc"],
                }
                for r in rows
            ],
        }

    @router.post("/api/v1/safety/incidents/{incident_id}/receipts")
    def record_delivery_receipt(
        incident_id: str,
        item: NotificationDeliveryIn,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        evidence = item.transport_evidence_id.strip()
        channel = item.channel.strip()
        if not evidence or not channel:
            raise HTTPException(status_code=422, detail="channel and transport_evidence_id are required")

        now_utc = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            inc = conn.execute("SELECT * FROM safety_incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            if inc is None or not is_subject_authorized(session["role"], session["allowed_subjects"], inc["subject_id"]):
                raise HTTPException(status_code=404, detail="Incident unavailable")

            rcpt = conn.execute(
                "SELECT * FROM safety_notification_receipts WHERE incident_id = ? AND channel = ?",
                (incident_id, channel),
            ).fetchone()
            if rcpt is None:
                receipt_id = f"rcpt-{uuid.uuid4().hex[:12]}"
                new_state = "ACKNOWLEDGED" if inc["status"] == "ACKNOWLEDGED" else "DELIVERED"
                conn.execute(
                    """
                    INSERT INTO safety_notification_receipts (
                        receipt_id, incident_id, channel, state, transport_evidence_id,
                        delivered_at_utc, acknowledged_at_utc, created_at_utc
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        receipt_id,
                        incident_id,
                        channel,
                        new_state,
                        evidence,
                        now_utc,
                        inc["acknowledged_at_utc"],
                        now_utc,
                    ),
                )
            else:
                receipt_id = rcpt["receipt_id"]
                new_state = "ACKNOWLEDGED" if rcpt["state"] == "ACKNOWLEDGED" else "DELIVERED"
                conn.execute(
                    """
                    UPDATE safety_notification_receipts
                    SET state = ?, transport_evidence_id = ?, delivered_at_utc = COALESCE(delivered_at_utc, ?)
                    WHERE receipt_id = ?
                    """,
                    (new_state, evidence, now_utc, receipt_id),
                )
            conn.commit()
        return {
            "receipt_id": receipt_id,
            "incident_id": incident_id,
            "channel": channel,
            "state": new_state,
            "transport_evidence_id": evidence,
            "delivered_at_utc": now_utc,
        }

    @router.get("/api/v1/safety/incidents/{incident_id}/receipts")
    def list_receipts(
        incident_id: str,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            inc = conn.execute("SELECT * FROM safety_incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            if inc is None or not is_subject_authorized(session["role"], session["allowed_subjects"], inc["subject_id"]):
                raise HTTPException(status_code=404, detail="Incident unavailable")
            rows = conn.execute(
                "SELECT * FROM safety_notification_receipts WHERE incident_id = ? ORDER BY created_at_utc ASC",
                (incident_id,),
            ).fetchall()
        return {
            "incident_id": incident_id,
            "items": [
                {
                    "receipt_id": r["receipt_id"],
                    "channel": r["channel"],
                    "state": r["state"],
                    "transport_evidence_id": r["transport_evidence_id"],
                    "delivered_at_utc": r["delivered_at_utc"],
                    "acknowledged_at_utc": r["acknowledged_at_utc"],
                    "created_at_utc": r["created_at_utc"],
                }
                for r in rows
            ],
        }

    @router.post("/api/v1/safety/incidents/{incident_id}/evaluate-timeout")
    def evaluate_incident_timeout(
        incident_id: str,
        item: TimeoutEvalIn,
        identity: tuple[dict, str] = Depends(require_session),
    ):
        session, _ = identity
        ref_now = (item.now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with sqlite3.connect(db_path()) as conn:
            conn.row_factory = sqlite3.Row
            _ensure_tables(conn)
            inc = conn.execute("SELECT * FROM safety_incidents WHERE incident_id = ?", (incident_id,)).fetchone()
            if inc is None or not is_subject_authorized(session["role"], session["allowed_subjects"], inc["subject_id"]):
                raise HTTPException(status_code=404, detail="Incident unavailable")

            created_dt = datetime.fromisoformat(inc["created_at_utc"]).astimezone(timezone.utc)
            elapsed = (ref_now - created_dt).total_seconds()
            timed_out = inc["status"] == "OPEN" and elapsed >= item.timeout_seconds
            esc_state = inc["escalation_state"]
            esc_at = inc["escalated_at_utc"]
            if timed_out:
                esc_state = "ESCALATED_PENDING_RESPONDER"
                esc_at = esc_at or ref_now.isoformat()
                conn.execute(
                    """
                    UPDATE safety_incidents
                    SET escalation_state = ?, escalated_at_utc = ?
                    WHERE incident_id = ?
                    """,
                    (esc_state, esc_at, incident_id),
                )
                conn.commit()
        return {
            "incident_id": incident_id,
            "status": inc["status"],
            "elapsed_seconds": round(elapsed, 3),
            "timeout_seconds": item.timeout_seconds,
            "timed_out": timed_out,
            "escalation_state": esc_state,
            "escalated_at_utc": esc_at,
            "responder_confirmed": False,
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

    @router.get("/api/v1/safety/offline-fallback")
    def offline_assistance_fallback(
        locale: Literal["vi", "en"] = Query("vi"),
        identity: tuple[dict, str] = Depends(require_session),
    ):
        _session, _ = identity
        if locale == "en":
            steps = [
                "Verify crewmember responsiveness and airway/breathing locally on board.",
                "Notify the onboard crew medical officer or nearby crewmates directly via local intercom.",
                "Record observations and actions in the local Care Journal while offline.",
                "Do not assume Ground/Earth delivery; sync queued events when link is restored.",
            ]
            notice = "Offline onboard fallback only. No message has been delivered to Earth or Mission Control."
        else:
            steps = [
                "Kiểm tra trực tiếp phản ứng và đường thở/nhịp thở của phi hành gia trên tàu.",
                "Báo trực tiếp cho sĩ quan y tế trên tàu hoặc đồng đội gần nhất qua liên lạc nội bộ.",
                "Ghi lại quan sát và hành động vào Nhật ký Chăm sóc cục bộ khi đang ngoại tuyến.",
                "Không mặc định tin đã gửi về Trái Đất; đồng bộ hàng đợi khi khôi phục kết nối.",
            ]
            notice = "Chỉ là hướng dẫn dự phòng ngoại tuyến trên tàu. Chưa có thông điệp nào được gửi về Trái Đất hoặc Trung tâm Điều khiển."
        return {
            "locale": locale,
            "relay_status": "OFFLINE_ONBOARD_ONLY",
            "earth_delivery_claimed": False,
            "requires_local_crew_followup": True,
            "notice": notice,
            "local_followup_steps": steps,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }

    return router
