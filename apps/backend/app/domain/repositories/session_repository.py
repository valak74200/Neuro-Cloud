from typing import List, Optional, Protocol

from app.domain.entities.capture_session import CaptureSession
from app.domain.entities.recall_card import RecallCard
from app.domain.entities.transcript_segment import TranscriptSegment


class SessionRepository(Protocol):
    def save(self, session: CaptureSession) -> CaptureSession: ...

    def get(self, session_id: str) -> Optional[CaptureSession]: ...

    def list_by_user(self, user_id: str) -> List[CaptureSession]: ...


class SegmentRepository(Protocol):
    def save(self, segment: TranscriptSegment) -> TranscriptSegment: ...

    def list_by_session(self, session_id: str) -> List[TranscriptSegment]: ...


class RecallCardRepository(Protocol):
    def save(self, card: RecallCard) -> RecallCard: ...

    def list_by_user(self, user_id: str) -> List[RecallCard]: ...
