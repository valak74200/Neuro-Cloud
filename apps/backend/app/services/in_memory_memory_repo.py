from typing import Dict, List

from app.domain.entities.memory import Memory
from app.domain.repositories.memory_repository import MemoryRepository


class InMemoryMemoryRepository(MemoryRepository):
    def __init__(self) -> None:
        self._store: Dict[str, List[Memory]] = {}

    def save(self, memory: Memory) -> Memory:
        self._store.setdefault(memory.user_id, []).append(memory)
        return memory

    def list_by_user(self, user_id: str) -> List[Memory]:
        return list(self._store.get(user_id, []))
