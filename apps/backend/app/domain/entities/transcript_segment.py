from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TranscriptSegment:
    id: str
    session_id: str
    start_ms: int
    end_ms: int
    text: str
    speaker_label: Optional[str] = None

    def __post_init__(self) -> None:
        if self.start_ms < 0 or self.end_ms < 0:
            raise ValueError("timestamps must be non-negative")
        if self.end_ms <= self.start_ms:
            raise ValueError("end_ms must be greater than start_ms")
        if not self.text:
            raise ValueError("text is required")
