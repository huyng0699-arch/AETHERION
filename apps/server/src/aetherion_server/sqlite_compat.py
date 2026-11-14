"""Windows-safe SQLite connection helpers that close connections on context exit."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any


class ClosingConnection(sqlite3.Connection):
    """sqlite3.Connection whose ``with`` block commits/rolls back and closes the file handle."""

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool | None:
        try:
            return super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()


def connect_closing(
    path: str | Path,
    *,
    timeout: float = 5.0,
    foreign_keys: bool = False,
) -> sqlite3.Connection:
    """Open a SQLite connection configured with Row factory and deterministic handle closure."""
    conn = sqlite3.connect(path, timeout=timeout, factory=ClosingConnection)
    conn.row_factory = sqlite3.Row
    if foreign_keys:
        conn.execute("PRAGMA foreign_keys = ON")
    return conn
