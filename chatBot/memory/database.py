import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("data/memory.db")


def create_connection(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    initialize_database(connection)
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    cursor = connection.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS session_messages ("
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "    thread_id TEXT NOT NULL,"
        "    role TEXT NOT NULL,"
        "    content TEXT NOT NULL,"
        "    created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS long_term_memories ("
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "    user_id TEXT NOT NULL,"
        "    memory_key TEXT NOT NULL,"
        "    memory_value TEXT NOT NULL,"
        "    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,"
        "    UNIQUE(user_id, memory_key)"
        ")"
    )
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS threads ("
        "    id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "    thread_id TEXT NOT NULL UNIQUE,"
        "    name TEXT NOT NULL DEFAULT '',"
        "    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,"
        "    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"
        ")"
    )
    connection.commit()
