"""Windows-safe SQLite connection helpers that close OS file handles deterministically."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Any


class ClosingConnection(sqlite3.Connection):
    """Commit/rollback on context exit and immediately close the underlying SQLite handle."""

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool | None:
        try:
            return super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()


def connect_sqlite(
    database: str | bytes | Path,
    *,
    timeout: float = 5.0,
    uri: bool = False,
    row_factory: Any = sqlite3.Row,
    foreign_keys: bool | None = None,
) -> ClosingConnection:
    """Open a SQLite connection whose context manager commits and closes OS handles."""
    conn = sqlite3.connect(
        database,
        timeout=timeout,
        uri=uri,
        factory=ClosingConnection,
    )
    if row_factory is not None:
        conn.row_factory = row_factory
    if foreign_keys is True:
        conn.execute("PRAGMA foreign_keys = ON")
    elif foreign_keys is False:
        conn.execute("PRAGMA foreign_keys = OFF")
    return conn
