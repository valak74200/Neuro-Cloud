from dataclasses import dataclass


@dataclass(frozen=True)
class DiarizationSegment:
    start_ms: int
    end_ms: int
    speaker_label: str

    def __post_init__(self) -> None:
        if self.start_ms < 0 or self.end_ms < 0:
            raise ValueError("timestamps must be non-negative")
        if self.end_ms <= self.start_ms:
            raise ValueError("end_ms must be greater than start_ms")
        if not self.speaker_label:
            raise ValueError("speaker_label is required")
