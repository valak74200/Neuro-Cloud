import os
from contextlib import contextmanager
from typing import Generator, List, Optional

from app.domain.entities.capture_session import SessionType
from app.domain.entities.user import User
from app.domain.repositories.memory_repository import MemoryRepository
from app.domain.repositories.session_repository import SessionRepository
from app.infrastructure.ai.openai_embeddings_provider import OpenAIEmbeddingsProvider
from app.infrastructure.auth.auth_middleware import get_current_user
from app.infrastructure.db.postgres import get_session_factory
from app.infrastructure.repositories.postgres_memory_repository import (
    PostgresMemoryRepository,
)
from app.infrastructure.storage.s3_storage import S3AudioStorage
from app.schemas.consent import ConsentCreateRequest, ConsentResponse
from app.schemas.data_lifecycle import ExportResponse, PurgeRequest, PurgeResponse
from app.schemas.memory import MemoryCreateRequest, MemoryResponse
from app.schemas.recall import RecallCardResponse
from app.schemas.search import SearchResult
from app.schemas.segment import SegmentCreateRequest, SegmentResponse
from app.schemas.session import SessionCreateRequest, SessionEndRequest, SessionResponse
from app.schemas.user import UserResponse
from app.services.consent_service import ConsentService, InMemoryConsentStore
from app.services.data_lifecycle_service import DataLifecycleService
from app.services.in_memory_memory_repo import InMemoryMemoryRepository
from app.services.in_memory_session_repo import InMemorySessionRepository
from app.services.index_embeddings_service import InMemoryVectorIndex
from app.services.proactive_recall_service import ProactiveRecallService
from app.services.record_segment_service import RecordSegmentService
from app.services.save_memory import SaveMemoryService
from app.services.search_memories_service import SearchMemoriesService
from app.services.session_service import SessionService
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

api = APIRouter(tags=["memories", "auth", "sessions", "consents"])


_memory_repo: InMemoryMemoryRepository | None = None


@contextmanager
def _get_repo_context() -> Generator[MemoryRepository, None, None]:
    """Return a repository instance, preferring Postgres if configured.

    Falls back to a shared in-memory repository if no NC_PG_DSN is configured.
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
        global _memory_repo
        if _memory_repo is None:
            _memory_repo = InMemoryMemoryRepository()
        yield _memory_repo


def get_memory_repository() -> MemoryRepository:
    with _get_repo_context() as repo:
        return repo


# Global in-memory session repository instance (for tests/dev)
_session_repo: SessionRepository = InMemorySessionRepository()
_segment_repo = None
_vector_index = InMemoryVectorIndex()
_embeddings_provider = None  # lazy init to avoid env errors at import time
_consent_store = InMemoryConsentStore()


def _get_embeddings_provider(safe: bool = True):
    global _embeddings_provider
    if _embeddings_provider is not None:
        return _embeddings_provider
    try:
        _embeddings_provider = OpenAIEmbeddingsProvider()
        return _embeddings_provider
    except Exception:
        if safe:
            return None
        raise


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
    description=(
        "Liste tous les souvenirs de l'utilisateur authentifié (pagination/filtre)."
    ),
    tags=["memories"],
)
def list_memories(
    current_user: User = Depends(get_current_user),
    repo: MemoryRepository = Depends(get_memory_repository),
    limit: int = 20,
    offset: int = 0,
    q: Optional[str] = None,
    source: Optional[str] = None,
    sort: Optional[str] = None,
) -> List[MemoryResponse]:
    items = repo.list_by_user(current_user.id)
    if source:
        items = [m for m in items if m.source == source]
    if q:
        ql = q.lower()
        items = [m for m in items if ql in (m.content or "").lower()]
    if sort:
        reverse = sort.startswith("-")
        key = sort[1:] if reverse else sort
        if key == "content":
            items.sort(key=lambda m: m.content or "", reverse=reverse)
    items = items[offset : offset + max(1, limit)]
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
    description="Liste toutes les sessions de l'utilisateur (pagination/filtre).",
    tags=["sessions"],
)
def list_sessions(
    current_user: User = Depends(get_current_user),
    repo: SessionRepository = Depends(get_session_repository),
    limit: int = 20,
    offset: int = 0,
    type: Optional[SessionType] = None,
) -> List[SessionResponse]:
    items = repo.list_by_user(current_user.id)
    if type:
        items = [s for s in items if s.type == type]
    items = items[offset : offset + max(1, limit)]
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
    # Indexation: toujours stocker l'item; embeddings si dispo
    metadata = {"session_id": seg.session_id, "text": seg.text}
    vector: List[float] = []
    provider = _get_embeddings_provider(safe=True)
    if provider is not None:
        try:
            vectors = provider.embed_texts([seg.text])
            if vectors:
                vector = vectors[0]
        except Exception:
            vector = []
    _vector_index.add(item_id=seg.id, vector=vector, metadata=metadata)
    return SegmentResponse(**seg.__dict__)


@api.get(
    "/sessions/{session_id}/segments",
    response_model=List[SegmentResponse],
    summary="Lister les segments",
    description="Liste les segments d'une session (pagination/filtre).",
    tags=["sessions"],
)
def list_segments(
    session_id: str,
    current_user: User = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    q: Optional[str] = None,
    speaker: Optional[str] = None,
):
    repo = get_segment_repository()
    items = repo.list_by_session(session_id)
    if speaker:
        items = [s for s in items if (s.speaker_label or "") == speaker]
    if q:
        ql = q.lower()
        items = [s for s in items if ql in (s.text or "").lower()]
    items = items[offset : offset + max(1, limit)]
    return [SegmentResponse(**s.__dict__) for s in items]


@api.post(
    "/consents",
    response_model=ConsentResponse,
    summary="Créer un consentement",
    description="Crée un enregistrement de consentement pour une session.",
    tags=["consents"],
)
def create_consent(
    req: ConsentCreateRequest,
    current_user: User = Depends(get_current_user),
):
    service = ConsentService(store=_consent_store)
    record = service.request_consent(
        session_id=req.session_id,
        participant_id=req.participant_id,
        method=req.method,
        granted=req.granted,
        timestamp_ms=req.timestamp_ms,
    )
    return ConsentResponse(**record.__dict__)


@api.get(
    "/consents",
    response_model=List[ConsentResponse],
    summary="Lister les consentements",
    description="Liste les consentements d'une session donnée.",
    tags=["consents"],
)
def list_consents(session_id: str, current_user: User = Depends(get_current_user)):
    service = ConsentService(store=_consent_store)
    items = service.list_session_consents(session_id=session_id)
    return [ConsentResponse(**r.__dict__) for r in items]


@api.get(
    "/recall/feed",
    response_model=List[RecallCardResponse],
    summary="Feed de rappels",
    description="Retourne des cartes à rappeler (importance, cooldown).",
    tags=["memories"],
)
def recall_feed(
    current_user: User = Depends(get_current_user),
) -> List[RecallCardResponse]:
    # Pour l’instant, on ne persiste pas les RecallCards; on retourne un feed vide
    service = ProactiveRecallService()
    cards = service.select(cards=[], last_recall_at={})
    return [
        RecallCardResponse(
            id=c.id,
            user_id=c.user_id,
            title=c.title,
            summary=c.summary,
            tags=[t.value for t in c.tags],
            importance=c.importance.score,
        )
        for c in cards
    ]


@api.get(
    "/search",
    response_model=List[SearchResult],
    summary="Recherche sémantique",
    description="Recherche de segments par similarité sémantique.",
    tags=["memories"],
)
def search(
    q: str, top_k: int = 5, session_id: Optional[str] = None
) -> List[SearchResult]:
    provider = _get_embeddings_provider(safe=True)
    meta_by_id = {item_id: meta for item_id, _, meta in _vector_index.items()}

    def build(pairs: List[tuple[str, float]]) -> List[SearchResult]:
        out: List[SearchResult] = []
        for item_id, score in pairs:
            meta = meta_by_id.get(item_id, {})
            out.append(
                SearchResult(
                    id=item_id,
                    score=score,
                    session_id=meta.get("session_id", ""),
                    text=meta.get("text", ""),
                )
            )
        return out

    # Fallback lexical si pas d'API embeddings
    if provider is None:
        ql = q.lower()
        pairs = [
            (item_id, 1.0)
            for item_id, _, meta in _vector_index.items()
            if ql in (meta.get("text") or "").lower()
            and (not session_id or meta.get("session_id") == session_id)
        ]
        return build(pairs[: max(1, top_k)])

    service = SearchMemoriesService(provider=provider, index=_vector_index)
    pairs = service.search(query=q, top_k=top_k)
    if not pairs:
        ql = q.lower()
        pairs = [
            (item_id, 1.0)
            for item_id, _, meta in _vector_index.items()
            if ql in (meta.get("text") or "").lower()
            and (not session_id or meta.get("session_id") == session_id)
        ]
        pairs = pairs[: max(1, top_k)]
    return build(pairs)


@api.get(
    "/export",
    response_model=ExportResponse,
    summary="Exporter les données utilisateur",
    description="Retourne tous les souvenirs de l'utilisateur.",
    tags=["memories"],
)
def export_data(
    current_user: User = Depends(get_current_user),
    repo: MemoryRepository = Depends(get_memory_repository),
) -> ExportResponse:
    service = DataLifecycleService(repo=repo)
    items = service.export_user_memories(user_id=current_user.id)
    return ExportResponse(
        items=[
            MemoryResponse(
                id=m.id, user_id=m.user_id, content=m.content, source=m.source
            )
            for m in items
        ]
    )


@api.post(
    "/purge",
    response_model=PurgeResponse,
    summary="Purger les données utilisateur",
    description="Supprime tous les souvenirs de l'utilisateur (in-memory).",
    tags=["memories"],
)
def purge_data(
    req: PurgeRequest,
    current_user: User = Depends(get_current_user),
    repo: MemoryRepository = Depends(get_memory_repository),
) -> PurgeResponse:
    if not req.confirm:
        return PurgeResponse(deleted=0)
    service = DataLifecycleService(repo=repo)
    deleted = service.purge_user_memories(user_id=current_user.id)
    return PurgeResponse(deleted=deleted)


@api.post(
    "/segments/upload",
    summary="Uploader un segment audio",
    description="Upload multipart d'un fichier audio vers S3/MinIO avec validations.",
    tags=["sessions"],
)
async def upload_segment(
    session_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    allowed_types = {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/ogg",
        "audio/webm",
    }
    content_type = file.content_type or "application/octet-stream"
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported content type: {content_type}",
        )

    data = await file.read()
    import os as _os
    import uuid as _uuid

    max_bytes = int(_os.getenv("NC_UPLOAD_MAX_BYTES", "25000000"))
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large",
        )

    ext = {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/ogg": ".ogg",
        "audio/webm": ".webm",
    }.get(content_type, "")
    key = f"users/{current_user.id}/sessions/{session_id}/{_uuid.uuid4()}{ext}"

    storage = S3AudioStorage()
    storage.put(key=key, data=data, content_type=content_type)

    return {"key": key, "content_type": content_type, "size_bytes": len(data)}
