from typing import List, Optional

from app.domain.entities.diarization_segment import DiarizationSegment
from app.domain.providers.diarization_provider import DiarizationProvider


class DiarizeSessionService:
    """Use case: Send audio to server diarization and return speaker segments."""

    def __init__(self, provider: DiarizationProvider) -> None:
        self._provider = provider

    def diarize(
        self, audio: bytes, language: Optional[str] = None
    ) -> List[DiarizationSegment]:
        return self._provider.diarize(audio, language=language)
