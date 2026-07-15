from pathlib import Path

from memory.database import DEFAULT_DB_PATH, create_connection
from memory.long_term import LongTermMemoryStore
from memory.models import MemoryContext
from memory.session import SessionMemoryStore


class MemoryManager:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH) -> None:
        self.connection = create_connection(db_path)
        self.session_store = SessionMemoryStore(self.connection)
        self.long_term_store = LongTermMemoryStore(self.connection)

    def build_conversation_input(
        self,
        context: MemoryContext,
        user_input: str,
    ) -> list[dict]:
        messages: list[dict] = []
        memory_prompt = self._build_long_term_memory_prompt(context.user_id)
        if memory_prompt:
            messages.append(
                {
                    "role": "system",
                    "content": memory_prompt,
                }
            )

        messages.extend(self.session_store.load_messages(context.thread_id))
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
