from dataclasses import dataclass
from typing import Literal
import uuid


MemorySource = Literal["manual", "hotword", "meeting", "course", "call"]


@dataclass(frozen=True)
class Memory:
    id: str
    user_id: str
    content: str
    source: MemorySource

    @staticmethod
    def create(user_id: str, content: str, source: MemorySource = "manual") -> "Memory":
        if not user_id or not content:
            raise ValueError("user_id and content are required")
        return Memory(id=str(uuid.uuid4()), user_id=user_id, content=content, source=source)
