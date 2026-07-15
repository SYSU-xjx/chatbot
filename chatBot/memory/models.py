from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryContext:
    user_id: str
    thread_id: str
