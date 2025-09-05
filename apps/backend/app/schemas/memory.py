from typing import Literal, Optional

from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    # Optional in authenticated flow (user taken from token),
    # required in unauthenticated tests.
    user_id: Optional[str] = None
    content: str = Field(..., min_length=1)
    source: Literal[
        "manual",
        "hotword",
        "meeting",
        "course",
        "call",
    ] = "manual"


class MemoryResponse(BaseModel):
    id: str
    user_id: str
    content: str
    source: str
