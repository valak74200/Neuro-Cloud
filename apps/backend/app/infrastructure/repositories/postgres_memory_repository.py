from typing import List

from app.domain.entities.memory import Memory
from app.domain.repositories.memory_repository import MemoryRepository
from app.infrastructure.models.memory import MemoryModel
from sqlalchemy import select
from sqlalchemy.orm import Session


class PostgresMemoryRepository(MemoryRepository):
    """SQLAlchemy-backed implementation of MemoryRepository.

    The repository is deliberately thin and mapping-free: it converts between
    the domain dataclass and the SQLAlchemy model without embedding business logic.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, memory: Memory) -> Memory:
        model = MemoryModel(
            id=memory.id,
            user_id=memory.user_id,
            content=memory.content,
            source=memory.source,
        )
        self._session.merge(model)
        self._session.commit()
        return memory

    def list_by_user(self, user_id: str) -> List[Memory]:
        stmt = select(MemoryModel).where(MemoryModel.user_id == user_id)
        rows = self._session.execute(stmt).scalars().all()
        return [
            Memory(
                id=row.id, user_id=row.user_id, content=row.content, source=row.source
            )
            for row in rows
        ]
