from typing import Dict, List, Optional

from app.domain.entities.capture_session import CaptureSession
from app.domain.entities.transcript_segment import TranscriptSegment
from app.domain.repositories.session_repository import (
    RecallCardRepository,
    SegmentRepository,
    SessionRepository,
)


class InMemorySessionRepository(SessionRepository):
    def __init__(self) -> None:
        self._by_id: Dict[str, CaptureSession] = {}
        self._by_user: Dict[str, List[str]] = {}

    def save(self, session: CaptureSession) -> CaptureSession:
        self._by_id[session.id] = session
        self._by_user.setdefault(session.user_id, [])
        if session.id not in self._by_user[session.user_id]:
            self._by_user[session.user_id].append(session.id)
        return session

    def get(self, session_id: str) -> Optional[CaptureSession]:
        return self._by_id.get(session_id)

    def list_by_user(self, user_id: str) -> List[CaptureSession]:
        return [self._by_id[sid] for sid in self._by_user.get(user_id, [])]


class InMemorySegmentRepository(SegmentRepository):
    def __init__(self) -> None:
        self._by_session: Dict[str, List[TranscriptSegment]] = {}

    def save(self, segment: TranscriptSegment) -> TranscriptSegment:
        self._by_session.setdefault(segment.session_id, []).append(segment)
        return segment

    def list_by_session(self, session_id: str) -> List[TranscriptSegment]:
        return list(self._by_session.get(session_id, []))


class InMemoryRecallCardRepository(RecallCardRepository):
    def __init__(self) -> None:
        self._by_user: Dict[str, List] = {}

    def save(self, card):
        from app.domain.entities.recall_card import RecallCard  # lazy import

        assert isinstance(card, RecallCard)
        self._by_user.setdefault(card.user_id, []).append(card)
        return card

    def list_by_user(self, user_id: str):
        return list(self._by_user.get(user_id, []))
