import sqlite3


class LongTermMemoryStore:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def save_memory(self, user_id: str, memory_key: str, memory_value: str) -> None:
        self.connection.execute(
            """
            INSERT INTO long_term_memories (user_id, memory_key, memory_value)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, memory_key)
            DO UPDATE SET
                memory_value = excluded.memory_value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, memory_key, memory_value),
        )
        self.connection.commit()

    def load_memories(self, user_id: str) -> dict[str, str]:
        rows = self.connection.execute(
            """
            SELECT memory_key, memory_value
            FROM long_term_memories
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
        return {row["memory_key"]: row["memory_value"] for row in rows}

    def forget_memory(self, user_id: str, memory_key: str) -> None:
        self.connection.execute(
            "DELETE FROM long_term_memories"
            " WHERE user_id = ? AND memory_key = ?",
            (user_id, memory_key),
        )
        self.connection.commit()

    def list_memory_keys(self, user_id: str) -> list[str]:
        rows = self.connection.execute(
            "SELECT memory_key FROM long_term_memories"
            " WHERE user_id = ?"
            " ORDER BY memory_key",
            (user_id,),
        ).fetchall()
        return [row["memory_key"] for row in rows]
