from dataclasses import dataclass
from typing import Literal

ConsentMethod = Literal["in_app", "voice_beep", "verbal"]


@dataclass(frozen=True)
class ConsentRecord:
    id: str
    session_id: str
    participant_id: str
    granted: bool
    method: ConsentMethod
    timestamp_ms: int

    def __post_init__(self) -> None:
        if not self.session_id or not self.participant_id:
            raise ValueError("session_id and participant_id are required")
        if self.timestamp_ms < 0:
            raise ValueError("timestamp_ms must be non-negative")
