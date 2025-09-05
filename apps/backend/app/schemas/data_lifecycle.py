from typing import List, Optional

from app.schemas.memory import MemoryResponse
from pydantic import BaseModel, Field


class ExportResponse(BaseModel):
    items: List[MemoryResponse] = Field(default_factory=list)


class PurgeRequest(BaseModel):
    confirm: Optional[bool] = Field(default=True)


class PurgeResponse(BaseModel):
    deleted: int
