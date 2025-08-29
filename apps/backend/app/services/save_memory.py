from app.domain.entities.memory import Memory, MemorySource
from app.domain.repositories.memory_repository import MemoryRepository


class SaveMemoryService:
    """Application service: orchestrates validation and persistence of a Memory."""

    def __init__(self, memory_repository: MemoryRepository) -> None:
        self._repo = memory_repository

    def save_memory(
        self, user_id: str, content: str, source: MemorySource = "manual"
    ) -> Memory:
        memory = Memory.create(user_id=user_id, content=content, source=source)
        return self._repo.save(memory)
