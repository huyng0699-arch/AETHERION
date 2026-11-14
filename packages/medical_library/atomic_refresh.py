"""Verified atomic replacement of an offline SQLite library."""
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile


def install_verified_library(candidate, destination, *, expected_sha256, expected_schema_version):
    source, target = Path(candidate), Path(destination)
    if not source.is_file() or source.resolve() == target.resolve():
        raise ValueError("Candidate must be a separate existing file")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != expected_sha256.lower():
        raise ValueError("Candidate SHA-256 mismatch")
    with sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity check failed")
        if db.execute("PRAGMA user_version").fetchone()[0] != expected_schema_version:
            raise ValueError("Unexpected schema version")
        if db.execute("PRAGMA foreign_key_check").fetchall():
            raise ValueError("Foreign-key violations")
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, prefix=".cliff-", suffix=".sqlite", delete=False) as out:
            staged = Path(out.name)
            with source.open("rb") as inp:
                while chunk := inp.read(1048576):
                    out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        if hashlib.sha256(staged.read_bytes()).hexdigest() != digest:
            raise IOError("Staged file SHA mismatch")
        if target.exists():
            backup = target.with_suffix(target.suffix + ".bak")
            os.replace(target, backup)
            try:
                os.replace(staged, target)
            except OSError:
                os.replace(backup, target)
                raise
        else:
            os.replace(staged, target)
        staged = None
        return digest
    finally:
        if staged is not None:
            staged.unlink(missing_ok=True)
