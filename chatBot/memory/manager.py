from pathlib import Path

from memory.database import DEFAULT_DB_PATH, create_connection
from memory.long_term import LongTermMemoryStore
from memory.models import MemoryContext
from memory.session import SessionMemoryStore


class MemoryManager:
    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB_PATH,
        context_window: int | None = 30,
    ) -> None:
        """context_window: max session messages to load per turn (None = unlimited)."""
        self.connection = create_connection(db_path)
        self.session_store = SessionMemoryStore(self.connection)
        self.long_term_store = LongTermMemoryStore(self.connection)
        self.context_window = context_window

    def build_conversation_input(
        self,
        context: MemoryContext,
        user_input: str,
    ) -> list[dict]:
        messages: list[dict] = []

        # Long-term memory as system prompt
        memory_prompt = self._build_long_term_memory_prompt(context.user_id)
        if memory_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": memory_prompt,
                }
            )

        # Session messages with context window limit
        messages.extend(
            self.session_store.load_messages(
                context.thread_id,
                max_messages=self.context_window,
            )
        )
        messages.append(
            {
                "role": "user",
                "content": user_input,
            }
        )
        return messages

    def save_turn(
        self,
        context: MemoryContext,
        user_input: str,
        assistant_output: str,
    ) -> None:
        self.session_store.append_message(context.thread_id, "user", user_input)
        self.session_store.append_message(
            context.thread_id,
            "assistant",
            assistant_output,
        )
        self.session_store.touch_thread(context.thread_id)

    def save_long_term_memory(
        self,
        context: MemoryContext,
        memory_key: str,
        memory_value: str,
    ) -> None:
        self.long_term_store.save_memory(
            context.user_id,
            memory_key,
            memory_value,
        )

    def _build_long_term_memory_prompt(self, user_id: str) -> str:
        memories = self.long_term_store.load_memories(user_id)
        if not memories:
            return ""

        memory_lines = [
            f"{memory_key}: {memory_value}"
            for memory_key, memory_value in memories.items()
        ]
        return (
            "Here are remembered user facts and preferences. "
            "Use them only when relevant.\n"
            + "\n".join(memory_lines)
        )

    # ── Thread helper methods ──────────────────────────────────────

    def create_thread(self, name: str = "") -> str:
        return self.session_store.create_thread(name)

    def ensure_thread(self, thread_id: str, name: str = "") -> str:
        """Get existing thread or create one with the given id."""
        return self.session_store.ensure_thread(thread_id, name)

    def list_threads(self) -> list[dict]:
        return self.session_store.list_threads()

    def get_thread(self, thread_id: str) -> dict | None:
        return self.session_store.get_thread(thread_id)

    def rename_thread(self, thread_id: str, name: str) -> None:
        self.session_store.rename_thread(thread_id, name)

    def delete_thread(self, thread_id: str) -> None:
        self.session_store.delete_thread(thread_id)

    def message_count(self, thread_id: str) -> int:
        row = self.connection.execute(
            "SELECT COUNT(*) AS cnt"
            " FROM session_messages"
            " WHERE thread_id = ?",
            (thread_id,),
        ).fetchone()
        return row["cnt"] if row else 0
