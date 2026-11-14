"""Local development test-data reset utility (Q-0043)."""

from pathlib import Path

from .sqlite_compat import connect_sqlite


def reset_development_test_data(db_path: Path | str, *, confirm: bool = False) -> int:
    """Delete only explicitly marked engineering_test TEST_FIXTURE rows; never touch other scopes."""
    if not confirm:
        raise ValueError("Explicit confirm=True is required before deleting development test data")

    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f"Database not found: {path}")

    with connect_sqlite(path) as conn:
        cur = conn.execute(
            """
            DELETE FROM observations
            WHERE scope = 'engineering_test'
              AND (source_id = 'test_fixture' OR source = 'test_fixture')
            """
        )
        conn.commit()
        return int(cur.rowcount)
