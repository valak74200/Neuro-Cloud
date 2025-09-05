import os
from contextlib import contextmanager
from typing import Generator, List

from app.domain.entities.user import User
from app.domain.repositories.memory_repository import MemoryRepository
from app.domain.repositories.session_repository import SessionRepository
from app.infrastructure.ai.openai_embeddings_provider import OpenAIEmbeddingsProvider
from app.infrastructure.auth.auth_middleware import get_current_user
from app.infrastructure.db.postgres import get_session_factory
from app.infrastructure.repositories.postgres_memory_repository import (
    PostgresMemoryRepository,
)
from app.schemas.memory import MemoryCreateRequest, MemoryResponse
from app.schemas.search import SearchResult
from app.schemas.segment import SegmentCreateRequest, SegmentResponse
from app.schemas.session import SessionCreateRequest, SessionEndRequest, SessionResponse
from app.schemas.user import UserResponse
from app.services.in_memory_memory_repo import InMemoryMemoryRepository
from app.services.in_memory_session_repo import InMemorySessionRepository
from app.services.index_embeddings_service import InMemoryVectorIndex
from app.services.record_segment_service import RecordSegmentService
from app.services.save_memory import SaveMemoryService
from app.services.search_memories_service import SearchMemoriesService
from app.services.session_service import SessionService
from fastapi import APIRouter, Depends

api = APIRouter(tags=["memories", "auth", "sessions"])


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


# Global in-memory session repository instance (for tests/dev)
_session_repo: SessionRepository = InMemorySessionRepository()
_segment_repo = None
_vector_index = InMemoryVectorIndex()
_embeddings_provider = OpenAIEmbeddingsProvider()


def get_session_repository() -> SessionRepository:
    return _session_repo


def get_segment_repository():
    # lazy import to avoid circulars
    global _segment_repo
    if _segment_repo is None:
        from app.services.in_memory_session_repo import InMemorySegmentRepository

        _segment_repo = InMemorySegmentRepository()
    return _segment_repo


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


@api.post(
    "/sessions",
    response_model=SessionResponse,
    summary="Démarrer une session",
    description="Crée une session de capture pour l'utilisateur authentifié.",
    tags=["sessions"],
)
def start_session(
    req: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    repo: SessionRepository = Depends(get_session_repository),
) -> SessionResponse:
    service = SessionService(session_repository=repo)
    session = service.start_session(
        user_id=current_user.id,
        session_type=req.type,
        started_at_ms=req.started_at_ms,
    )
    return SessionResponse(**session.__dict__)


@api.post(
    "/sessions/{session_id}/end",
    response_model=SessionResponse,
    summary="Terminer une session",
    description="Termine une session de capture en cours.",
    tags=["sessions"],
)
def end_session(
    session_id: str,
    req: SessionEndRequest,
    current_user: User = Depends(get_current_user),
    repo: SessionRepository = Depends(get_session_repository),
) -> SessionResponse:
    service = SessionService(session_repository=repo)
    session = service.end_session(session_id=session_id, ended_at_ms=req.ended_at_ms)
    return SessionResponse(**session.__dict__)


@api.get(
    "/sessions",
    response_model=List[SessionResponse],
    summary="Lister les sessions",
    description="Liste toutes les sessions de l'utilisateur.",
    tags=["sessions"],
)
def list_sessions(
    current_user: User = Depends(get_current_user),
    repo: SessionRepository = Depends(get_session_repository),
) -> List[SessionResponse]:
    items = repo.list_by_user(current_user.id)
    return [SessionResponse(**s.__dict__) for s in items]


@api.post(
    "/segments",
    response_model=SegmentResponse,
    summary="Créer un segment",
    description="Crée un segment de transcription attaché à une session.",
    tags=["sessions"],
)
def create_segment(
    req: SegmentCreateRequest,
    current_user: User = Depends(get_current_user),
    sessions: SessionRepository = Depends(get_session_repository),
):
    service = RecordSegmentService(
        session_repo=sessions, segment_repo=get_segment_repository()
    )
    seg = service.record_segment(
        session_id=req.session_id,
        start_ms=req.start_ms,
        end_ms=req.end_ms,
        text=req.text,
        speaker_label=req.speaker_label,
    )
    # Indexation sémantique (best-effort)
    try:
        vectors = _embeddings_provider.embed_texts([seg.text])
        if vectors:
            _vector_index.add(
                item_id=seg.id,
                vector=vectors[0],
                metadata={"session_id": seg.session_id, "text": seg.text},
            )
    except Exception:
        # Pas d'indexation si provider indisponible
        pass
    return SegmentResponse(**seg.__dict__)


@api.get(
    "/sessions/{session_id}/segments",
    response_model=List[SegmentResponse],
    summary="Lister les segments",
    description="Liste les segments d'une session.",
    tags=["sessions"],
)
def list_segments(
    session_id: str,
    current_user: User = Depends(get_current_user),
):
    repo = get_segment_repository()
    items = repo.list_by_session(session_id)
    return [SegmentResponse(**s.__dict__) for s in items]


@api.get(
    "/search",
    response_model=List[SearchResult],
    summary="Recherche sémantique",
    description="Recherche de segments par similarité sémantique.",
    tags=["memories"],
)
def search(q: str, top_k: int = 5) -> List[SearchResult]:
    service = SearchMemoriesService(provider=_embeddings_provider, index=_vector_index)
    pairs = service.search(query=q, top_k=top_k)
    # Construire la réponse avec le texte et session_id si présents
    meta_by_id = {item_id: meta for item_id, _, meta in _vector_index.items()}
    results: List[SearchResult] = []
    for item_id, score in pairs:
        meta = meta_by_id.get(item_id, {})
        results.append(
            SearchResult(
                id=item_id,
                score=score,
                session_id=meta.get("session_id", ""),
                text=meta.get("text", ""),
            )
        )
    return results
