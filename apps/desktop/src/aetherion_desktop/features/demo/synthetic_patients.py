"""Deterministic offline AETHERION patient fixtures, never real NASA/patient data.

This module has no FastAPI dependency, never opens the canonical health store,
and never promotes synthetic measurements to VERIFIED or live telemetry.
"""
from __future__ import annotations

from contextlib import closing
from datetime import date, datetime, timedelta, timezone
import math
import os
from pathlib import Path
import random
import sqlite3

DATASET_ID = "AETHERION-SYNTHETIC-PATIENTS-V1"
DAYS = 540
SOURCE_ID = "AETHERION_SYNTHETIC_GENERATOR_V1"
SUBJECTS = (
    ("DEMO-P001", "Sample Patient 01", 29, 62.0),
    ("DEMO-P002", "Sample Patient 02", 37, 69.0),
    ("DEMO-P003", "Sample Patient 03", 48, 76.0),
    ("DEMO-P004", "Sample Patient 04", 56, 81.0),
    ("DEMO-P005", "Sample Patient 05", 63, 73.0),
)
# Metric names/units are data identifiers. Visible strings use central i18n.
METRICS = (
    ("heart_rate", "bpm"),
    ("spo2", "%"),
    ("body_temperature", "degC"),
    ("body_mass", "kg"),
    ("sleep_duration", "h"),
    ("fatigue_score", "scale_1_10"),
    ("steps", "count"),
    ("respiratory_rate", "breaths/min"),
    ("systolic_bp", "mmHg"),
    ("diastolic_bp", "mmHg"),
    ("blood_glucose", "mg/dL"),
    ("hydration_ml", "mL"),
)
METRIC_UNITS = dict(METRICS)


def demo_path() -> Path:
    """Use a dedicated user-owned DB, not the server database."""
    return Path.home() / ".aetherion" / "demo" / "synthetic_patients_v1.sqlite3"


def _safe_path(path: str | Path | None) -> Path:
    resolved = Path(path) if path is not None else demo_path()
    resolved = resolved.expanduser().resolve()
    # Even a mistaken environment configuration must not create a fixture in
    # the canonical AETHERION health database.
    names = ("AETHERION_DB_PATH", "AETHERION_DATABASE_PATH")
    for name in names:
        value = os.getenv(name, "").strip()
        if value and resolved == Path(value).expanduser().resolve():
            raise ValueError("Synthetic database path conflicts with health data")
    return resolved


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            return super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()


def _connection(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path), timeout=20, factory=_ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS demo_metadata (
        dataset_id TEXT PRIMARY KEY, schema_version INTEGER NOT NULL,
        generated_for_day TEXT NOT NULL, synthetic INTEGER NOT NULL CHECK(synthetic = 1)
    );
    CREATE TABLE IF NOT EXISTS demo_subjects (
        subject_id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
        age INTEGER NOT NULL, synthetic INTEGER NOT NULL CHECK(synthetic = 1)
    );
    CREATE TABLE IF NOT EXISTS demo_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id TEXT NOT NULL REFERENCES demo_subjects(subject_id),
        observed_at TEXT NOT NULL, day_utc TEXT NOT NULL,
        metric TEXT NOT NULL, value REAL NOT NULL, unit TEXT NOT NULL,
        source_id TEXT NOT NULL, scope TEXT NOT NULL
            CHECK(scope = 'engineering_test'),
        verification_state TEXT NOT NULL CHECK(verification_state = 'TEST_FIXTURE'),
        quality TEXT NOT NULL CHECK(quality = 'UNVERIFIED'),
        synthetic INTEGER NOT NULL CHECK(synthetic = 1),
        UNIQUE(subject_id, observed_at, metric)
    );
    CREATE INDEX IF NOT EXISTS demo_obs_subject_metric_date
        ON demo_observations(subject_id, metric, day_utc);
    CREATE INDEX IF NOT EXISTS demo_obs_subject_day
        ON demo_observations(subject_id, day_utc);
    """)


def _validate_existing(conn: sqlite3.Connection) -> bool:
    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )}
    if not tables:
        return False
    required = {"demo_metadata", "demo_subjects", "demo_observations"}
    if not required.issubset(tables) or tables - required:
        raise ValueError("Refusing to modify a database not owned by synthetic demo")
    row = conn.execute(
        "SELECT dataset_id, schema_version, synthetic FROM demo_metadata"
    ).fetchone()
    if row is None or tuple(row) != (DATASET_ID, 1, 1):
        raise ValueError("Not an AETHERION synthetic demo database")
    return True


def _synthetic_values(patient_index: int, day: int, base_mass: float, rng: random.Random):
    """Plausible *fictional* fluctuations only, never clinical interpretation."""
    wave = math.sin(day * 0.125 + patient_index * 1.7)
    slow = math.sin(day * 0.022 + patient_index)
    active = math.sin(day * 0.047 + patient_index * 0.8)
    noise = lambda sigma: rng.gauss(0, sigma)
    clamp = lambda x, low, high: max(low, min(high, x))
    return {
        "heart_rate": round(clamp(67 + patient_index * 1.4 + wave*5 + noise(3), 48, 116), 1),
        "spo2": round(clamp(98.2 - patient_index*.13 + noise(.55), 94, 100), 1),
        "body_temperature": round(clamp(36.7 + slow*.18 + noise(.15), 35.8, 38.0), 2),
        "body_mass": round(clamp(base_mass + day*.003 + slow*.8 + noise(.25), 40, 130), 1),
        "sleep_duration": round(clamp(7.3 + active*.9 + noise(.65), 3.5, 10.5), 2),
        "fatigue_score": round(clamp(4 + patient_index*.23 - active*1.4 + noise(.95), 1, 10), 1),
        "steps": float(int(clamp(7600 + active*2200 + noise(1700), 500, 19000))),
        "respiratory_rate": round(clamp(15.5 + wave*1.2 + noise(1.1), 9, 25), 1),
        "systolic_bp": round(clamp(113 + patient_index*4.3 + slow*5 + noise(5), 87, 160), 1),
        "diastolic_bp": round(clamp(70 + patient_index*2.3 + slow*2 + noise(3.4), 51, 105), 1),
        "blood_glucose": round(clamp(91 + patient_index*2.1 + active*7 + noise(8), 65, 160), 1),
        "hydration_ml": float(int(clamp(2050 + active*320 + noise(260), 650, 3900))),
    }


def build_demo_database(
    path: str | Path | None = None, *, reset: bool = False, today: date | None = None
) -> dict:
    """Idempotent 540-day seed. Only writes to positively identified demo DBs."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    day = today or datetime.now(timezone.utc).date()
    with closing(_connection(target)) as conn:
        initialized = _validate_existing(conn)
        if not initialized:
            _schema(conn)
        row = conn.execute(
            "SELECT generated_for_day FROM demo_metadata WHERE dataset_id=?", (DATASET_ID,)
        ).fetchone()
        if (initialized and row is not None and row["generated_for_day"] == day.isoformat()
                and not reset):
            return demo_stats(target)
        rng = random.Random(724118)
        start = day - timedelta(days=DAYS - 1)
        with conn:
            conn.execute("DELETE FROM demo_observations")
            conn.execute("DELETE FROM demo_subjects")
            conn.execute("DELETE FROM demo_metadata")
            conn.execute(
                "INSERT INTO demo_metadata VALUES (?, 1, ?, 1)", (DATASET_ID, day.isoformat())
            )
            conn.executemany(
                "INSERT INTO demo_subjects VALUES (?, ?, ?, 1)",
                ((sid, name, age) for sid, name, age, _ in SUBJECTS)
            )
            batch = []
            for pi, (subject_id, _, _, mass) in enumerate(SUBJECTS):
                for di in range(DAYS):
                    current = start + timedelta(days=di)
                    data = _synthetic_values(pi, di, mass, rng)
                    for mi, (metric, unit) in enumerate(METRICS):
                        # Intentional sparse missing rows to exercise NO_DATA states.
                        if (di + 5*pi + 3*mi) % 41 == 0:
                            continue
                        observed = datetime(
                            current.year, current.month, current.day, 8 + mi // 4,
                            (mi % 4) * 11, tzinfo=timezone.utc
                        ).isoformat()
                        batch.append((
                            subject_id, observed, current.isoformat(), metric,
                            data[metric], unit, SOURCE_ID, "engineering_test",
                            "TEST_FIXTURE", "UNVERIFIED", 1,
                        ))
                        if len(batch) >= 1500:
                            conn.executemany(
                                "INSERT INTO demo_observations "
                                "(subject_id, observed_at, day_utc, metric, value, unit, "
                                "source_id, scope, verification_state, quality, synthetic) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch
                            )
                            batch.clear()
            if batch:
                conn.executemany(
                    "INSERT INTO demo_observations "
                    "(subject_id, observed_at, day_utc, metric, value, unit, "
                    "source_id, scope, verification_state, quality, synthetic) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)", batch
                )
    return demo_stats(target)


def _verified_connection(path: str | Path | None = None) -> sqlite3.Connection:
    target = _safe_path(path)
    if not target.is_file():
        raise FileNotFoundError("Synthetic demo has not been loaded")
    conn = _connection(target)
    try:
        if not _validate_existing(conn):
            raise ValueError("Empty synthetic demo database")
    except Exception:
        conn.close()
        raise
    return conn


def demo_stats(path: str | Path | None = None) -> dict:
    with closing(_verified_connection(path)) as conn:
        row = conn.execute("SELECT generated_for_day FROM demo_metadata").fetchone()
        points = conn.execute("SELECT COUNT(*) FROM demo_observations").fetchone()[0]
        count = conn.execute("SELECT COUNT(*) FROM demo_subjects").fetchone()[0]
        span = conn.execute(
            "SELECT MIN(day_utc), MAX(day_utc) FROM demo_observations"
        ).fetchone()
        return {
            "dataset_id": DATASET_ID, "is_synthetic": True,
            "subjects": count, "days": DAYS, "metrics": len(METRICS),
            "observations": points, "from": span[0], "to": span[1],
            "generated_for_day": row[0], "source": SOURCE_ID,
        }


def subjects(path: str | Path | None = None) -> list[dict]:
    with closing(_verified_connection(path)) as conn:
        return [dict(row) for row in conn.execute(
            "SELECT subject_id, display_name, age, synthetic "
            "FROM demo_subjects ORDER BY subject_id"
        )]


def series(subject_id: str, metric: str, *, limit: int = DAYS,
           path: str | Path | None = None, end_day: str | None = None) -> list[dict]:
    """Return an exact calendar-day series, including explicit missing days.

    Each record has state MEASURED or NO_DATA. NO_DATA is a *display-only*
    absence marker, never inserted into observations or claimed as a sensor
    measurement. An N-day window means N calendar days, not N recorded rows.
    """
    if metric not in METRIC_UNITS or not isinstance(limit, int) or not 1 <= limit <= DAYS:
        raise ValueError("Invalid metric or date range")
    with closing(_verified_connection(path)) as conn:
        metadata = conn.execute(
            "SELECT generated_for_day FROM demo_metadata WHERE dataset_id=?",
            (DATASET_ID,)
        ).fetchone()
        if metadata is None:
            raise ValueError("Synthetic dataset metadata missing")
        last = date.fromisoformat(metadata["generated_for_day"])
        first = last - timedelta(days=DAYS - 1)
        end = date.fromisoformat(end_day) if end_day is not None else last
        if not first <= end <= last:
            raise ValueError("Date outside synthetic dataset")
        start = max(first, end - timedelta(days=limit - 1))
        measured = {
            row["day_utc"]: dict(row)
            for row in conn.execute(
                "SELECT day_utc, value, unit, source_id, verification_state "
                "FROM demo_observations WHERE subject_id=? AND metric=? "
                "AND day_utc BETWEEN ? AND ? ORDER BY day_utc",
                (subject_id, metric, start.isoformat(), end.isoformat())
            )
        }
        output = []
        count = (end - start).days + 1
        for offset in range(count):
            day_utc = (start + timedelta(days=offset)).isoformat()
            if day_utc in measured:
                record = measured[day_utc]
                record["state"] = "MEASURED"
            else:
                record = {
                    "day_utc": day_utc,
                    "value": None,
                    "unit": METRIC_UNITS[metric],
                    "source_id": None,
                    "verification_state": None,
                    "state": "NO_DATA",
                }
            output.append(record)
        return output


def day_values(subject_id: str, chosen_day: str,
               path: str | Path | None = None) -> list[dict]:
    date.fromisoformat(chosen_day)
    with closing(_verified_connection(path)) as conn:
        rows = conn.execute(
            "SELECT metric, value, unit, observed_at, source_id, quality, "
            "verification_state FROM demo_observations "
            "WHERE subject_id=? AND day_utc=? ORDER BY metric",
            (subject_id, chosen_day)
        )
        return [dict(row) for row in rows]


def latest(subject_id: str, path: str | Path | None = None) -> list[dict]:
    with closing(_verified_connection(path)) as conn:
        rows = conn.execute(
            "SELECT o.metric, o.value, o.unit, o.day_utc, o.source_id "
            "FROM demo_observations AS o WHERE o.subject_id=? AND o.id=("
            "SELECT j.id FROM demo_observations AS j "
            "WHERE j.subject_id=o.subject_id AND j.metric=o.metric "
            "ORDER BY j.observed_at DESC LIMIT 1) ORDER BY o.metric",
            (subject_id,)
        )
        return [dict(row) for row in rows]
