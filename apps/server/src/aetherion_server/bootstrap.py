"""Offline bootstrap utility for local AETHERION operator and crew accounts."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

from .store import count_users, initialize, upsert_user


def default_database_path() -> Path:
    default = Path.home() / ".aetherion" / "observations.sqlite3"
    return Path(os.environ.get("AETHERION_DB_PATH", str(default)))


def ensure_bootstrap_user(
    db_path: str | Path,
    *,
    username: str,
    password: str,
    role: str = "operator",
    allowed_subjects: list[str] | None = None,
) -> dict:
    initialize(db_path)
    subjects = allowed_subjects if allowed_subjects is not None else (["*"] if role in {"operator", "admin", "flight_surgeon"} else [username])
    return upsert_user(
        db_path,
        username=username,
        password=password,
        role=role,
        allowed_subjects=subjects,
    )


def bootstrap_from_env(db_path: str | Path | None = None) -> dict | None:
    target = Path(db_path) if db_path else default_database_path()
    initialize(target)
    username = os.environ.get("AETHERION_BOOTSTRAP_USER", "").strip()
    password = os.environ.get("AETHERION_BOOTSTRAP_PASSWORD", "")
    role = os.environ.get("AETHERION_BOOTSTRAP_ROLE", "operator").strip() or "operator"
    subjects_raw = os.environ.get("AETHERION_BOOTSTRAP_SUBJECTS", "").strip()
    if not username or not password:
        return None
    if count_users(target) > 0:
        return None
    allowed_subjects = [s.strip() for s in subjects_raw.split(",") if s.strip()] if subjects_raw else None
    return ensure_bootstrap_user(
        target,
        username=username,
        password=password,
        role=role,
        allowed_subjects=allowed_subjects,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap an offline AETHERION server account.")
    parser.add_argument("--db", default=str(default_database_path()), help="SQLite database path")
    parser.add_argument("--username", required=True, help="Account username")
    parser.add_argument("--password", required=True, help="Account password (min 8 chars)")
    parser.add_argument("--role", default="operator", choices=["crew", "operator", "flight_surgeon", "admin"])
    parser.add_argument(
        "--subjects",
        default="*",
        help="Comma-separated allowed subject IDs (or '*' for authorized operators)",
    )
    args = parser.parse_args(argv)
    subjects = [s.strip() for s in args.subjects.split(",") if s.strip()]
    user = ensure_bootstrap_user(
        args.db,
        username=args.username,
        password=args.password,
        role=args.role,
        allowed_subjects=subjects,
    )
    print(f"Bootstrapped user '{user['username']}' (role={user['role']}, subjects={user['allowed_subjects']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
