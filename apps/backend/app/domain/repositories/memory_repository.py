from abc import ABC, abstractmethod
from typing import Protocol, List

from app.domain.entities.memory import Memory


class MemoryRepository(Protocol):
    def save(self, memory: Memory) -> Memory:
        ...

    def list_by_user(self, user_id: str) -> List[Memory]:
        ...
