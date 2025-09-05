from typing import Optional

from pydantic import BaseModel, Field


class SegmentCreateRequest(BaseModel):
    session_id: str = Field(..., description="Identifiant de session")
    start_ms: int = Field(..., ge=0)
    end_ms: int = Field(..., ge=0)
    text: str = Field(..., min_length=1)
    speaker_label: Optional[str] = None


class SegmentResponse(BaseModel):
    id: str
    session_id: str
    start_ms: int
    end_ms: int
    text: str
    speaker_label: Optional[str] = None
