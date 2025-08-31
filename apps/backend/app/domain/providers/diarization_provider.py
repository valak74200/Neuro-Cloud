from typing import List, Optional, Protocol

from app.domain.entities.diarization_segment import DiarizationSegment


class DiarizationProvider(Protocol):
    def diarize(
        self, audio: bytes, language: Optional[str] = None
    ) -> List[DiarizationSegment]: ...
