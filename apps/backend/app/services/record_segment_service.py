import uuid
from typing import Optional

from app.domain.entities.transcript_segment import TranscriptSegment
from app.domain.repositories.session_repository import (
    SegmentRepository,
    SessionRepository,
)


class RecordSegmentService:
    """Use case to attach a new transcript segment to a session."""

    def __init__(
        self, session_repo: SessionRepository, segment_repo: SegmentRepository
    ) -> None:
        self._sessions = session_repo
        self._segments = segment_repo

    def record_segment(
        self,
        session_id: str,
        start_ms: int,
        end_ms: int,
        text: str,
        speaker_label: Optional[str] = None,
    ) -> TranscriptSegment:
        if self._sessions.get(session_id) is None:
            raise ValueError("session not found")
        seg = TranscriptSegment(
            id=str(uuid.uuid4()),
            session_id=session_id,
            start_ms=start_ms,
            end_ms=end_ms,
            text=text,
            speaker_label=speaker_label,
        )
        return self._segments.save(seg)
