"""Server-owned administration state: one canonical SQLite, no duplicate engine.

No health records are forwarded to an AI provider. Local model discovery
contacts only a literal loopback address; cloud networking is not implemented.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from .store import check_readiness, initialize

DEFAULT_AI = {
    "mode": "off",
    "local_runtime": "ollama",
    "local_url": "http://127.0.0.1:11434",
    "local_model": "",
    "timeout_seconds": 5,
    "cloud_data_sharing": False,
}
SUPPORTED_AI_MODES = frozenset({"off", "local_only"})


def _db(path: str | Path):
    connection = sqlite3.connect(str(path), timeout=5)
    connection.row_factory = sqlite3.Row
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def initialize_admin(path: str | Path) -> None:
    initialize(path)
    with closing(_db(path)) as db:
        with db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS admin_settings "
                "(name TEXT PRIMARY KEY, value_json TEXT NOT NULL, updated_at TEXT NOT NULL, updated_by TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS admin_events "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, occurred_at TEXT NOT NULL, "
                "actor TEXT NOT NULL, action TEXT NOT NULL, outcome TEXT NOT NULL)"
            )


def validate_local_url(url: str) -> str:
    """Only literal IPv4/IPv6 loopback; no DNS, userinfo, path or redirects."""
    parsed = urlsplit(url.strip())
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "::1"}:
        raise ValueError("Local AI URL must use http://127.0.0.1 or http://[::1]")
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise ValueError("Local AI URL cannot contain credentials, path, query or fragment")
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Local AI port is invalid") from exc
    if port is None or not 1 <= port <= 65535:
        raise ValueError("Local AI URL must include a valid port")
    host = "127.0.0.1" if parsed.hostname == "127.0.0.1" else "[::1]"
    return f"http://{host}:{port}"


def read_ai_settings(path: str | Path) -> dict:
    initialize_admin(path)
    with closing(_db(path)) as db:
        row = db.execute("SELECT value_json FROM admin_settings WHERE name = 'ai'").fetchone()
    if row is None:
        return dict(DEFAULT_AI)
    try:
        saved = json.loads(row["value_json"])
        if not isinstance(saved, dict) or saved.get("mode", "off") not in SUPPORTED_AI_MODES:
            return dict(DEFAULT_AI)
        if saved.get("cloud_data_sharing", False) is not False:
            return dict(DEFAULT_AI)
        return {**DEFAULT_AI, **{key: saved[key] for key in DEFAULT_AI if key in saved}}
    except (ValueError, TypeError, KeyError):
        # Corruption must not silently activate AI.
        return dict(DEFAULT_AI)


def record_event(path: str | Path, *, actor: str, action: str, outcome: str) -> None:
    initialize_admin(path)
    with closing(_db(path)) as db:
        with db:
            db.execute("INSERT INTO admin_events(occurred_at,actor,action,outcome) VALUES(?,?,?,?)",
                       (_now(), actor, action, outcome))


def save_ai_settings(path: str | Path, settings: dict, *, actor: str) -> dict:
    """Allowlist every key and fail closed for cloud use."""
    if set(settings) != set(DEFAULT_AI):
        raise ValueError("AI settings schema mismatch")
    if settings["mode"] not in SUPPORTED_AI_MODES:
        raise ValueError("Cloud gateway is not installed; only OFF or LOCAL_ONLY can be activated")
    if settings["local_runtime"] != "ollama":
        raise ValueError("Only Ollama runtime is currently supported")
    normalized = dict(settings)
    normalized["local_url"] = validate_local_url(str(settings["local_url"]))
    model = settings["local_model"]
    if not isinstance(model, str) or len(model) > 120 or any(ord(c) < 32 for c in model):
        raise ValueError("Invalid local model name")
    normalized["local_model"] = model.strip()
    if normalized["mode"] == "local_only" and not normalized["local_model"]:
        raise ValueError("Select a real local model before enabling LOCAL_ONLY")
    if type(settings["timeout_seconds"]) is not int or not 1 <= settings["timeout_seconds"] <= 30:
        raise ValueError("Timeout must be an integer between 1 and 30 seconds")
    if settings["cloud_data_sharing"] is not False:
        raise ValueError("Cloud data sharing is disabled until a consent-aware gateway exists")
    initialize_admin(path)
    with closing(_db(path)) as db:
        with db:
            db.execute("INSERT INTO admin_settings(name,value_json,updated_at,updated_by) VALUES('ai',?,?,?) "
                       "ON CONFLICT(name) DO UPDATE SET value_json=excluded.value_json, "
                       "updated_at=excluded.updated_at,updated_by=excluded.updated_by",
                       (json.dumps(normalized, sort_keys=True), _now(), actor))
            db.execute("INSERT INTO admin_events(occurred_at,actor,action,outcome) VALUES(?,?,?,?)",
                       (_now(), actor, "ai.settings.update", "saved"))
    return normalized


def probe_local_ai(settings: dict) -> dict:
    """Real Ollama /api/tags call; a reachable daemon is NOT model readiness."""
    try:
        base = validate_local_url(str(settings["local_url"]))
        request = Request(base + "/api/tags", headers={"Accept": "application/json"})
        # Do not follow redirects: they could bypass loopback restrictions.
        from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
        class RejectRedirect(HTTPRedirectHandler):
            def redirect_request(self, request, fp, code, msg, headers, newurl):
                return None
        opener = build_opener(ProxyHandler({}), RejectRedirect())
        with opener.open(request, timeout=min(3, int(settings["timeout_seconds"]))) as reply:
            if reply.status != 200:
                raise ValueError(f"Runtime HTTP {reply.status}")
            data = reply.read(256_000)
        payload = json.loads(data)
        models = sorted({
            item["name"] for item in payload.get("models", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        })
        selected = str(settings.get("local_model", "")).strip()
        return {
            "runtime": "ollama", "connection": "READY",
            "model_ready": bool(selected and selected in models),
            "selected_model": selected, "models": models, "error": None,
        }
    except (OSError, ValueError, TypeError, KeyError, HTTPError, URLError) as exc:
        return {
            "runtime": "ollama", "connection": "OFFLINE",
            "model_ready": False,
            "selected_model": settings.get("local_model") or "",
            "models": [], "error": str(exc)[:240],
        }




def test_local_model(settings: dict) -> dict:
    """Run a bounded, PHI-free Ollama inference; daemon ping alone is insufficient."""
    available = probe_local_ai(settings)
    if not available["model_ready"]:
        return {"status": "UNAVAILABLE", "model": available["selected_model"],
                "reason": available.get("error") or "Selected model is not installed"}
    request_data = json.dumps({
        "model": available["selected_model"], "stream": False,
        "prompt": "Return the single word AETHERION_READY. No other text.",
        "options": {"temperature": 0, "num_predict": 24},
    }).encode("utf-8")
    request = Request(validate_local_url(settings["local_url"]) + "/api/generate",
                      data=request_data, method="POST",
                      headers={"Content-Type": "application/json", "Accept": "application/json"})
    from urllib.request import build_opener, HTTPRedirectHandler, ProxyHandler
    class RejectRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, fp, code, msg, headers, newurl):
            return None
    try:
        opener = build_opener(ProxyHandler({}), RejectRedirect())
        with opener.open(request, timeout=int(settings["timeout_seconds"])) as reply:
            if reply.status != 200:
                raise ValueError(f"Model HTTP {reply.status}")
            payload = json.loads(reply.read(100_000))
        generated = payload.get("response")
        if not isinstance(generated, str) or not generated.strip() or payload.get("done") is not True:
            raise ValueError("Model returned no complete answer")
        return {"status": "READY", "model": available["selected_model"],
                "response_received": True, "personal_data_sent": False}
    except (OSError, ValueError, TypeError, KeyError, HTTPError, URLError) as exc:
        return {"status": "ERROR", "model": available["selected_model"],
                "response_received": False, "reason": str(exc)[:240]}

def system_overview(path: str | Path) -> dict:
    """Admin-only facts from the canonical server database; no synthetic health values."""
    readiness = check_readiness(path)
    initialize_admin(path)
    with closing(_db(path)) as db:
        counts = {}
        for table in ("users", "subjects", "observations"):
            counts[table] = int(db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    root = Path(__file__).resolve().parents[4]
    records_dir = root / "knowledge" / "nasa" / "cliff_119_2023" / "records"
    db_library = root / "knowledge" / "nasa" / "cliff_119_2023" / "AETHERION_NASA_CLIFF_119.sqlite"
    return {
        "service": "aetherion-server", "api_version": "0.2.0",
        "database": readiness["database"], "counts": counts,
        "ai": read_ai_settings(path),
        "knowledge": {
            "nasa_source_json_records": sum(1 for _ in records_dir.glob("*.json")) if records_dir.is_dir() else None,
            "offline_library_present": db_library.is_file(),
            "note": "File presence is not clinical/source verification.",
        },
        "subsystems": {
            "http": "READY", "sqlite": "READY",
            "local_ai": "NOT_CHECKED", "cloud_ai": "NOT_CONFIGURED",
            "devices": "NO_ADAPTER_CONNECTED", "telegram": "DISABLED",
            "mobile": "NOT_CONNECTED", "watch": "NOT_CONNECTED",
        },
    }


def recent_admin_events(path: str | Path, limit: int = 30) -> list[dict]:
    initialize_admin(path)
    with closing(_db(path)) as db:
        rows = db.execute("SELECT occurred_at,actor,action,outcome FROM admin_events "
                          "ORDER BY id DESC LIMIT ?", (max(1, min(100, limit)),)).fetchall()
    return [dict(row) for row in rows]


def list_observed_sources(path: str | Path) -> dict:
    """Inventory ONLY source IDs from persisted observations, not paired devices.

    A previously recorded source is not evidence of an active sensor.
    """
    initialize_admin(path)
    with closing(_db(path)) as db:
        rows = db.execute(
            "SELECT source_id, COUNT(*) AS records, "
            "COUNT(DISTINCT subject_id) AS subjects, MAX(observed_at) AS last_observed_at, "
            "MAX(received_at) AS last_received_at "
            "FROM observations GROUP BY source_id "
            "ORDER BY last_received_at DESC LIMIT 200"
        ).fetchall()
    return {
        "sources": [
            {"source_id": row["source_id"], "stored_records": row["records"],
             "subjects_count": row["subjects"],
             "last_observed_at": row["last_observed_at"],
             "last_received_at": row["last_received_at"],
             "connection_state": "NOT_VERIFIED"} for row in rows
        ],
        "connected_devices": None,
        "note": "Historical source IDs do not prove a connected physical device.",
    }


def list_admin_users(path: str | Path) -> dict:
    """Redacted account inventory; password hashes and session tokens excluded."""
    initialize_admin(path)
    with closing(_db(path)) as db:
        rows = db.execute(
            "SELECT username, role, allowed_subjects_json, active, created_at "
            "FROM users ORDER BY username COLLATE NOCASE LIMIT 500"
        ).fetchall()
    return {"users": [
        {"username": row["username"], "role": row["role"],
         "allowed_subjects": json.loads(row["allowed_subjects_json"]),
         "active": bool(row["active"]), "created_at": row["created_at"]}
        for row in rows
    ]}


def backup_sqlite(path: str | Path, *, actor: str) -> dict:
    """Consistent online SQLite snapshot without exposing an arbitrary write path."""
    target = Path(path)
    initialize_admin(target)
    folder = target.parent / "backups"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    # UTC microseconds to avoid overwriting another snapshot.
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = folder / f"aetherion-{stamp}.sqlite3"
    with closing(_db(target)) as source, closing(_db(destination)) as output:
        source.backup(output)
        result = output.execute("PRAGMA integrity_check").fetchone()[0]
    if result != "ok":
        destination.unlink(missing_ok=True)
        raise RuntimeError("Backup integrity check failed")
    record_event(target, actor=actor, action="sqlite.backup", outcome="created")
    return {"status": "created", "filename": destination.name, "integrity": result}
