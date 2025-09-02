from __future__ import annotations

from dataclasses import dataclass
from typing import List

from app.domain.entities.memory import Memory
from app.domain.repositories.memory_repository import MemoryRepository


@dataclass(frozen=True)
class PurgePolicy:
    by_user: bool = True


class DataLifecycleService:
    def __init__(self, repo: MemoryRepository) -> None:
        self._repo = repo

    def export_user_memories(self, user_id: str) -> List[Memory]:
        return list(self._repo.list_by_user(user_id))

    def purge_user_memories(
        self, user_id: str, policy: PurgePolicy | None = None
    ) -> int:
        # In-memory only: supprime tout pour l'utilisateur
        policy = policy or PurgePolicy()
        if not policy.by_user:
            return 0
        memories = list(self._repo.list_by_user(user_id))
        # Essayer de supprimer via méthode facultative du repo
        deleted = 0
        for m in memories:
            delete = getattr(self._repo, "delete", None)
            if callable(delete):
                delete(m.id)
                deleted += 1
        return deleted
