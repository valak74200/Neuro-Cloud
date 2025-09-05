from typing import Literal, Optional

from pydantic import BaseModel, Field


class SessionCreateRequest(BaseModel):
    type: Literal["meeting", "course", "call", "personal"] = Field(
        ..., description="Type de session"
    )
    started_at_ms: int = Field(..., ge=0, description="Horodatage départ (ms)")


class SessionEndRequest(BaseModel):
    ended_at_ms: int = Field(..., ge=0, description="Horodatage fin (ms)")


class SessionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    started_at_ms: int
    ended_at_ms: Optional[int] = None
