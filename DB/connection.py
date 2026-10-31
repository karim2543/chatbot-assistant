import sqlite3
from contextlib import contextmanager
from typing import Union


DatabasePath = Union[str, bytes]


def connect(database_path: DatabasePath, timeout: float = 5.0) -> sqlite3.Connection:
    """Open a SQLite connection with the project-wide safety settings."""
    connection = sqlite3.connect(database_path, timeout=timeout)
    connection.execute("PRAGMA foreign_keys = ON;")
    return connection


@contextmanager
def transaction(database_path: DatabasePath, timeout: float = 5.0):
    connection = connect(database_path, timeout=timeout)
    try:
        with connection:
            yield connection
    finally:
        connection.close()
