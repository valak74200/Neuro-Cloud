import uuid
from dataclasses import replace
from typing import Optional

from app.domain.entities.capture_session import CaptureSession, SessionType
from app.domain.repositories.session_repository import SessionRepository


class SessionService:
    """Use cases to start and end capture sessions."""

    def __init__(self, session_repository: SessionRepository) -> None:
        self._sessions = session_repository

    def start_session(
        self, user_id: str, session_type: SessionType, started_at_ms: int
    ) -> CaptureSession:
        if not user_id:
            raise ValueError("user_id required")
        session = CaptureSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=session_type,
            started_at_ms=started_at_ms,
        )
        return self._sessions.save(session)

    def end_session(self, session_id: str, ended_at_ms: int) -> CaptureSession:
        existing: Optional[CaptureSession] = self._sessions.get(session_id)
        if existing is None:
            raise ValueError("session not found")
        updated = replace(existing, ended_at_ms=ended_at_ms)
        # CaptureSession.__post_init__ validates ordering
        return self._sessions.save(updated)
