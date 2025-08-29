from typing import List, Protocol

from app.domain.entities.memory import Memory


class MemoryRepository(Protocol):
    def save(self, memory: Memory) -> Memory: ...

    def list_by_user(self, user_id: str) -> List[Memory]: ...
