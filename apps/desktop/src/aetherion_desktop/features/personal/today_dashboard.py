"""Personal Today real dashboard model and native PySide6 view (Q-0076).

Healthy users open the Personal Today dashboard directly without forced symptom
intake. Every displayed measurement carries explicit source, timestamp, unit,
scope, and quality semantics (READY, NO_DATA, STALE, OFFLINE, DENIED, ERROR,
UNVERIFIED). Historical NASA research is never presented as live telemetry.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import math
from typing import Any
from urllib.parse import urlencode
import urllib.request

VALID_QUALITY = frozenset({"READY", "NO_DATA", "STALE", "OFFLINE", "DENIED", "ERROR", "UNVERIFIED"})
DEFAULT_STALE_AFTER = timedelta(hours=24)


@dataclass(frozen=True)
class PersonalObservationCard:
    metric: str
    reading: str
    unit: str
    observed_at: str
    source_id: str
    scope: str
    quality: str
    verification_state: str


@dataclass(frozen=True)
class PersonalTodaySnapshot:
    state: str
    subject_id: str
    cards: tuple[PersonalObservationCard, ...]
    latest_at: str
    intake_required: bool
    care_flow_stage: str
    status_note: str
    has_more: bool = False


def personal_observations_url(api_url: str, subject_id: str) -> str:
    """Build a canonical, injection-safe observations URL for a personal subject."""
    cleaned = subject_id.strip()
    if not (1 <= len(cleaned) <= 80) or any(ord(c) < 32 for c in cleaned):
        raise ValueError("subject_id must be 1..80 printable characters")
    return f"{api_url.rstrip('/')}/api/v1/observations?{urlencode({'subject_id': cleaned, 'limit': 50})}"


def aggregate_observation_quality(cards: tuple[PersonalObservationCard, ...] | list[PersonalObservationCard]) -> str:
    """Choose a conservative data-availability label, never a health verdict.

    A READY observation denotes an accepted data record, not a healthy person.
    An unknown/unverified entry must not make the entire screen look READY.
    """
    if not cards:
        return "NO_DATA"
    qualities = {str(card.quality).upper() for card in cards}
    if qualities - VALID_QUALITY:
        return "ERROR"
    for critical in ("ERROR", "DENIED", "OFFLINE", "UNVERIFIED"):
        if critical in qualities:
            return critical
    if "STALE" in qualities:
        return "STALE"
    if "NO_DATA" in qualities:
        return "NO_DATA" if qualities == {"NO_DATA"} else "UNVERIFIED"
    return "READY" if qualities == {"READY"} else "UNVERIFIED"


def build_personal_today_snapshot(
    payload: object,
    subject_id: str,
    *,
    now: datetime | None = None,
    stale_after: timedelta = DEFAULT_STALE_AFTER,
    offline: bool = False,
    denied: bool = False,
) -> PersonalTodaySnapshot:
    """Build a Personal Today snapshot with fail-closed provenance and missing-data semantics.

    Healthy users open the dashboard with ``intake_required=False`` even when
    no symptoms are logged. Missing sensor or check-in data yields ``NO_DATA``,
    never an inferred illness or unconsciousness claim.
    """
    if offline:
        return PersonalTodaySnapshot(
            state="OFFLINE",
            subject_id=subject_id,
            cards=(),
            latest_at="",
            intake_required=False,
            care_flow_stage="GATHER",
            status_note="Server unreachable (OFFLINE). Local cached state not fabricated.",
        )
    if denied:
        return PersonalTodaySnapshot(
            state="DENIED",
            subject_id=subject_id,
            cards=(),
            latest_at="",
            intake_required=False,
            care_flow_stage="GATHER",
            status_note="Access denied by server policy (DENIED).",
        )
    if not isinstance(payload, dict) or payload.get("subject_id") != subject_id:
        return PersonalTodaySnapshot(
            state="ERROR",
            subject_id=subject_id,
            cards=(),
            latest_at="",
            intake_required=False,
            care_flow_stage="GATHER",
            status_note="Response subject mismatch or malformed payload (ERROR).",
        )
    observations = payload.get("observations")
    if (not isinstance(observations, list) or len(observations) > 500 or
            not isinstance(payload.get("has_more", False), bool)):
        return PersonalTodaySnapshot(
            state="ERROR",
            subject_id=subject_id,
            cards=(),
            latest_at="",
            intake_required=False,
            care_flow_stage="GATHER",
            status_note="Missing observations array (ERROR).",
        )
    if not observations:
        return PersonalTodaySnapshot(
            state="NO_DATA",
            subject_id=subject_id,
            cards=(),
            latest_at="",
            intake_required=False,
            care_flow_stage="GATHER",
            status_note="No personal observations recorded today (NO_DATA). Symptom intake is optional.",
            has_more=bool(payload.get("has_more", False)),
        )

    ref_now = now or datetime.now(timezone.utc)
    if ref_now.tzinfo is None:
        raise ValueError("Reference clock must be timezone-aware")

    cards: list[PersonalObservationCard] = []
    latest_dt: datetime | None = None
    excluded_nonlive = 0
    for item in observations:
        if not isinstance(item, dict) or item.get("subject_id") != subject_id:
            return PersonalTodaySnapshot(
                state="ERROR",
                subject_id=subject_id,
                cards=(),
                latest_at="",
                intake_required=False,
                care_flow_stage="GATHER",
                status_note="Observation identity mismatch (ERROR).",
            )
        # Research cohorts, synthetic engineering records and test fixtures are
        # never personal vital signs, even if their imported quality says READY.
        # Validate subject identity ABOVE this filter to fail closed on mixed IDs.
        source_name = str(item.get("source_id") or "").casefold()
        scope_name = str(item.get("scope") or "").casefold()
        verification_name = str(item.get("verification_state") or "").upper()
        if (scope_name in {"engineering_test", "test_fixture"} or
                verification_name == "TEST_FIXTURE" or
                source_name.startswith(("nasa_osdr:", "research:"))):
            excluded_nonlive += 1
            continue
        required = ("metric", "value", "unit", "observed_at", "source_id", "scope", "quality", "verification_state")
        if any(item.get(k) is None or str(item[k]).strip() == "" for k in required):
            return PersonalTodaySnapshot(
                state="ERROR",
                subject_id=subject_id,
                cards=(),
                latest_at="",
                intake_required=False,
                care_flow_stage="GATHER",
                status_note="Observation lacks required provenance fields (ERROR).",
            )
        try:
            if isinstance(item["value"], bool) or not isinstance(item["value"], (int, float)):
                raise ValueError("measurement must be numeric, not boolean or arbitrary text")
            val = float(item["value"])
            if not math.isfinite(val):
                raise ValueError("nonfinite")
            obs_dt = datetime.fromisoformat(str(item["observed_at"]).replace("Z", "+00:00"))
            if obs_dt.tzinfo is None or obs_dt.utcoffset() is None:
                raise ValueError("naive timestamp")
            # The current API stores receipt provenance. Keep compatibility
            # with older evidence fixtures without received_at, but reject
            # fabricated or inconsistent receipt times when they are supplied.
            if item.get("received_at") is not None:
                received_dt = datetime.fromisoformat(str(item["received_at"]).replace("Z", "+00:00"))
                if (received_dt.tzinfo is None or received_dt.utcoffset() is None or
                        received_dt < obs_dt):
                    raise ValueError("invalid received_at provenance")
        except (ValueError, TypeError, OverflowError):
            return PersonalTodaySnapshot(
                state="ERROR",
                subject_id=subject_id,
                cards=(),
                latest_at="",
                intake_required=False,
                care_flow_stage="GATHER",
                status_note="Invalid observation value or timestamp (ERROR).",
            )

        quality = str(item["quality"]).upper()
        if quality in {"ERROR", "DENIED", "OFFLINE"}:
            # A server may report availability problems, but a numeric payload
            # carrying DENIED/ERROR/OFFLINE must not expose a personal reading.
            return PersonalTodaySnapshot(
                state="ERROR", subject_id=subject_id, cards=(), latest_at="",
                intake_required=False, care_flow_stage="GATHER",
                status_note="Invalid availability state mixed with measurement (ERROR).",
            )
        if quality == "NO_DATA":
            continue
        if quality not in VALID_QUALITY:
            quality = "UNVERIFIED"
        ver_state = str(item["verification_state"])
        if quality == "READY" and ver_state != "VERIFIED":
            quality = "UNVERIFIED"
        if obs_dt > ref_now:
            quality = "UNVERIFIED"
        elif quality == "READY" and (ref_now - obs_dt) > stale_after:
            quality = "STALE"

        if latest_dt is None or obs_dt > latest_dt:
            latest_dt = obs_dt

        cards.append(
            PersonalObservationCard(
                metric=str(item["metric"]),
                reading=f"{val:g} {item['unit']}",
                unit=str(item["unit"]),
                observed_at=obs_dt.isoformat(),
                source_id=str(item["source_id"]),
                scope=str(item["scope"]),
                quality=quality,
                verification_state=ver_state,
            )
        )

    if not cards:
        return PersonalTodaySnapshot(
            state="NO_DATA", subject_id=subject_id, cards=(), latest_at="",
            intake_required=False, care_flow_stage="GATHER",
            status_note=("No live personal observations; research/test fixtures excluded (NO_DATA)."
                         if excluded_nonlive else
                         "No usable recorded personal observations (NO_DATA)."),
            has_more=payload.get("has_more", False),
        )
    overall_state = aggregate_observation_quality(cards)
    state_notes = {
        "READY": "Source-backed readings available; this is not a health assessment.",
        "STALE": "Some readings are stale; request a newer measurement before interpreting change.",
        "UNVERIFIED": "Some readings are unverified or conflicting; no health conclusion is implied.",
        "OFFLINE": "The data source is offline; last readings cannot prove current health.",
        "DENIED": "Access to some data is denied; no unavailable values are inferred.",
        "ERROR": "The source contains invalid data; do not interpret these readings.",
        "NO_DATA": "No usable recorded measurements; unknown does not mean normal.",
    }
    return PersonalTodaySnapshot(
        state=overall_state,
        subject_id=subject_id,
        cards=tuple(cards),
        latest_at=latest_dt.isoformat() if latest_dt else "",
        intake_required=False,
        care_flow_stage="RECHECK" if cards else "GATHER",
        status_note=state_notes[overall_state],
        has_more=bool(payload.get("has_more", False)),
    )


def submit_personal_checkin(
    api_url: str,
    subject_id: str,
    metric: str,
    value: float,
    unit: str,
    *,
    note: str = "",
    now: datetime | None = None,
    opener: Any = None,
) -> dict[str, Any]:
    """Submit a voluntary self-reported check-in to the canonical server."""
    if not math.isfinite(float(value)):
        raise ValueError("value must be finite")
    obs_time = (now or datetime.now(timezone.utc)).isoformat()
    body = {
        "subject_id": subject_id.strip(),
        "metric": metric.strip(),
        "value": float(value),
        "unit": unit.strip(),
        "observed_at": obs_time,
        "source_id": "personal_self_checkin",
        "scope": "PERSONAL",
        "quality": "UNVERIFIED",
        "verification_state": "SELF_REPORTED",
        "note": note.strip(),
    }
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/api/v1/observations",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    fetch = opener or urllib.request.urlopen
    with fetch(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_personal_today_widget(api_url: str, subject_id: str) -> Any:
    """Construct the native PySide6 Personal Today widget (lazy Qt import)."""
    from PySide6 import QtWidgets  # type: ignore

    widget = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(widget)

    header = QtWidgets.QLabel(f"Personal Today — Subject: {subject_id}")
    status_label = QtWidgets.QLabel("Status: READY (No forced symptom intake; click Refresh to sync)")
    table = QtWidgets.QTableWidget(0, 5)
    table.setHorizontalHeaderLabels(["Metric", "Reading", "Observed (UTC)", "Source", "Quality"])

    btn_row = QtWidgets.QHBoxLayout()
    refresh_btn = QtWidgets.QPushButton("Refresh / Recheck")
    optional_intake_btn = QtWidgets.QPushButton("Optional Symptom Check-In")
    btn_row.addWidget(refresh_btn)
    btn_row.addWidget(optional_intake_btn)

    layout.addWidget(header)
    layout.addWidget(status_label)
    layout.addLayout(btn_row)
    layout.addWidget(table)

    def refresh() -> None:
        try:
            url = personal_observations_url(api_url, subject_id)
            with urllib.request.urlopen(url, timeout=5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            snap = build_personal_today_snapshot(payload, subject_id)
        except Exception as exc:  # noqa: BLE001
            snap = build_personal_today_snapshot({}, subject_id, offline=True)
            status_label.setText(f"Status: {snap.state} ({exc})")
            return
        status_label.setText(f"Status: {snap.state} | {snap.status_note}")
        table.setRowCount(len(snap.cards))
        for r, card in enumerate(snap.cards):
            table.setItem(r, 0, QtWidgets.QTableWidgetItem(card.metric))
            table.setItem(r, 1, QtWidgets.QTableWidgetItem(card.reading))
            table.setItem(r, 2, QtWidgets.QTableWidgetItem(card.observed_at))
            table.setItem(r, 3, QtWidgets.QTableWidgetItem(card.source_id))
            table.setItem(r, 4, QtWidgets.QTableWidgetItem(card.quality))

    refresh_btn.clicked.connect(refresh)
    return widget
