import os
from contextlib import contextmanager
from typing import Generator

from app.domain.repositories.memory_repository import MemoryRepository
from app.infrastructure.db.postgres import get_session_factory
from app.infrastructure.repositories.postgres_memory_repository import (
    PostgresMemoryRepository,
)
from app.schemas.memory import MemoryCreateRequest, MemoryResponse
from app.services.in_memory_memory_repo import InMemoryMemoryRepository
from app.services.save_memory import SaveMemoryService
from fastapi import APIRouter, Depends

api = APIRouter()


@contextmanager
def _get_repo_context() -> Generator[MemoryRepository, None, None]:
    """Return a repository instance, preferring Postgres if configured.

    Falls back to in-memory repository if no NC_PG_DSN is configured.
    """
    dsn = os.getenv("NC_PG_DSN")
    if dsn:
        SessionFactory = get_session_factory()
        session = SessionFactory()
        try:
            yield PostgresMemoryRepository(session)
        finally:
            session.close()
    else:
        yield InMemoryMemoryRepository()


def get_memory_repository() -> MemoryRepository:
    with _get_repo_context() as repo:
        return repo


@api.post("/memories", response_model=MemoryResponse)
def create_memory(
    req: MemoryCreateRequest, repo: MemoryRepository = Depends(get_memory_repository)
) -> MemoryResponse:
    service = SaveMemoryService(memory_repository=repo)
    memory = service.save_memory(
        user_id=req.user_id, content=req.content, source=req.source
    )
    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        content=memory.content,
        source=memory.source,
    )
