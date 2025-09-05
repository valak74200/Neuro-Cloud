import os
from contextlib import contextmanager
from typing import Generator, List

from app.domain.entities.user import User
from app.domain.repositories.memory_repository import MemoryRepository
from app.infrastructure.auth.auth_middleware import get_current_user
from app.infrastructure.db.postgres import get_session_factory
from app.infrastructure.repositories.postgres_memory_repository import (
    PostgresMemoryRepository,
)
from app.schemas.memory import MemoryCreateRequest, MemoryResponse
from app.schemas.user import UserResponse
from app.services.in_memory_memory_repo import InMemoryMemoryRepository
from app.services.save_memory import SaveMemoryService
from fastapi import APIRouter, Depends

api = APIRouter(tags=["memories", "auth"])


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


@api.post(
    "/memories",
    response_model=MemoryResponse,
    summary="Créer un souvenir",
    description="Crée un souvenir pour l'utilisateur authentifié.",
    tags=["memories"],
)
def create_memory(
    req: MemoryCreateRequest,
    current_user: User = Depends(get_current_user),
    repo: MemoryRepository = Depends(get_memory_repository),
) -> MemoryResponse:
    """Create a new memory for the authenticated user.

    The `user_id` from the request body is ignored.
    """
    service = SaveMemoryService(memory_repository=repo)
    memory = service.save_memory(
        user_id=current_user.id,
        content=req.content,
        source=req.source,
    )
    return MemoryResponse(
        id=memory.id,
        user_id=memory.user_id,
        content=memory.content,
        source=memory.source,
    )


@api.get(
    "/me",
    response_model=UserResponse,
    summary="Utilisateur courant",
    description="Retourne les informations de l'utilisateur authentifié.",
    tags=["auth"],
)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Get information about the currently authenticated user."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
    )


@api.get(
    "/memories",
    response_model=List[MemoryResponse],
    summary="Lister les souvenirs",
    description="Liste tous les souvenirs de l'utilisateur authentifié.",
    tags=["memories"],
)
def list_memories(
    current_user: User = Depends(get_current_user),
    repo: MemoryRepository = Depends(get_memory_repository),
) -> List[MemoryResponse]:
    """List all memories for the authenticated user."""
    items = repo.list_by_user(current_user.id)
    return [
        MemoryResponse(id=m.id, user_id=m.user_id, content=m.content, source=m.source)
        for m in items
    ]
