from pydantic import BaseModel, Field
from typing import Literal


class MemoryCreateRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    source: Literal["manual", "hotword", "meeting", "course", "call"] = "manual"


class MemoryResponse(BaseModel):
    id: str
    user_id: str
    content: str
    source: str
