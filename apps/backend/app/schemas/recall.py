from typing import List

from pydantic import BaseModel, Field


class RecallCardResponse(BaseModel):
    id: str
    user_id: str
    title: str
    summary: str
    tags: List[str] = Field(default_factory=list)
    importance: float
