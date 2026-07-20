import sqlite3
from datetime import datetime, timezone
from uuid import uuid4


class SessionMemoryStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def append_message(
        self, thread_id: str, role: str, content: str
    ) -> None:
        self.connection.execute(
            "INSERT INTO session_messages (thread_id, role, content)"
            " VALUES (?, ?, ?)",
            (thread_id, role, content),
        )
        self.connection.commit()

    def load_messages(
        self, thread_id: str, max_messages: int | None = None
    ) -> list[dict]:
        if max_messages is not None and max_messages > 0:
            rows = self.connection.execute(
                "SELECT role, content FROM ("
                "    SELECT role, content, id"
                "    FROM session_messages"
                "    WHERE thread_id = ?"
                "    ORDER BY id DESC"
                "    LIMIT ?"
                ") ORDER BY id ASC",
                (thread_id, max_messages),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT role, content"
                " FROM session_messages"
                " WHERE thread_id = ?"
                " ORDER BY id",
                (thread_id,),
            ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

    # ── Thread management ──────────────────────────────────────────

    def create_thread(self, name: str = "") -> str:
        thread_id = uuid4().hex[:12]
        return self._insert_thread(thread_id, name)

    def _insert_thread(self, thread_id: str, name: str) -> str:
        self.connection.execute(
            "INSERT INTO threads (thread_id, name) VALUES (?, ?)"
            " ON CONFLICT(thread_id) DO NOTHING",
            (thread_id, name or "New Thread"),
        )
        self.connection.commit()
        return thread_id

    def ensure_thread(self, thread_id: str, name: str = "") -> str:
        """Get existing thread or create one with the given id."""
        existing = self.get_thread(thread_id)
        if existing:
            return thread_id
        return self._insert_thread(thread_id, name)

    def list_threads(self) -> list[dict]:
        rows = self.connection.execute(
            "SELECT thread_id, name, created_at, updated_at"
            " FROM threads"
            " ORDER BY updated_at DESC"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_thread(self, thread_id: str) -> dict | None:
        row = self.connection.execute(
            "SELECT thread_id, name, created_at, updated_at"
            " FROM threads"
            " WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
        return dict(row) if row else None

    def rename_thread(self, thread_id: str, name: str) -> None:
        self.connection.execute(
            "UPDATE threads SET name = ?, updated_at = ?"
            " WHERE thread_id = ?",
            (name, datetime.now(timezone.utc), thread_id),
        )
        self.connection.commit()

    def touch_thread(self, thread_id: str) -> None:
        """Update updated_at without changing name."""
        self.connection.execute(
            "UPDATE threads SET updated_at = ? WHERE thread_id = ?",
            (datetime.now(timezone.utc), thread_id),
        )
        self.connection.commit()

    def delete_thread(self, thread_id: str) -> None:
        self.connection.execute(
            "DELETE FROM session_messages WHERE thread_id = ?",
            (thread_id,),
        )
        self.connection.execute(
            "DELETE FROM threads WHERE thread_id = ?",
            (thread_id,),
        )
        self.connection.commit()
