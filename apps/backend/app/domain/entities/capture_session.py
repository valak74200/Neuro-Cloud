from dataclasses import dataclass
from typing import Literal, Optional

SessionType = Literal["meeting", "course", "call", "personal"]


@dataclass(frozen=True)
class CaptureSession:
    id: str
    user_id: str
    type: SessionType
    started_at_ms: int
    ended_at_ms: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id required")
        if self.started_at_ms < 0:
            raise ValueError("started_at_ms must be non-negative")
        if self.ended_at_ms is not None and self.ended_at_ms <= self.started_at_ms:
            raise ValueError("ended_at_ms must be greater than started_at_ms")
