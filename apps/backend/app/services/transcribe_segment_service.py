from typing import Optional

from app.domain.entities.transcript_segment import TranscriptSegment
from app.domain.providers.transcription_provider import TranscriptionProvider
from app.domain.repositories.session_repository import SegmentRepository


class TranscribeSegmentService:
    """Use case to transcribe a recorded audio segment (mocked provider)."""

    def __init__(
        self, provider: TranscriptionProvider, segments: SegmentRepository
    ) -> None:
        self._provider = provider
        self._segments = segments

    def transcribe_segment(
        self, segment: TranscriptSegment, audio: bytes, language: Optional[str] = None
    ) -> TranscriptSegment:
        text = self._provider.transcribe(audio, language=language)
        # Return a new segment with text replaced
        return TranscriptSegment(
            id=segment.id,
            session_id=segment.session_id,
            start_ms=segment.start_ms,
            end_ms=segment.end_ms,
            text=text,
            speaker_label=segment.speaker_label,
        )
