from typing import Literal

from pydantic import BaseModel, Field


class ConsentCreateRequest(BaseModel):
    session_id: str = Field(...)
    participant_id: str = Field(...)
    method: Literal["in_app", "voice_beep", "verbal"] = Field(...)
    granted: bool = Field(...)
    timestamp_ms: int = Field(..., ge=0)


class ConsentResponse(BaseModel):
    id: str
    session_id: str
    participant_id: str
    method: str
    granted: bool
    timestamp_ms: int
