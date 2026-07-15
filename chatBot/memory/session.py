import sqlite3


class SessionMemoryStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def append_message(self, thread_id: str, role: str, content: str) -> None:
        self.connection.execute(
            """
            INSERT INTO session_messages (thread_id, role, content)
            VALUES (?, ?, ?)
            """,
            (thread_id, role, content),
        )
        self.connection.commit()

    def load_messages(self, thread_id: str) -> list[dict]:
        rows = self.connection.execute(
            """
            SELECT role, content
            FROM session_messages
            WHERE thread_id = ?
            ORDER BY id
            """,
            (thread_id,),
        ).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]
