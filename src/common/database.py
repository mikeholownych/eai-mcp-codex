"""Database utilities using SQLite for local persistence."""

from sqlite3 import Connection, connect


def get_connection(dsn: str) -> Connection:
    """Return a SQLite connection."""
    conn = connect(dsn, check_same_thread=False)
    conn.row_factory = lambda cursor, row: {
        cursor.description[idx][0]: value for idx, value in enumerate(row)
    }
    return conn
