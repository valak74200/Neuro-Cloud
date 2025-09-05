from typing import Optional

from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    id: str = Field(description="Identifiant de la ressource (segment)")
    score: float = Field(description="Score de pertinence")
    session_id: str = Field(description="Session associée")
    text: str = Field(description="Contenu textuel du segment")


class SearchQuery(BaseModel):
    q: str
    session_id: Optional[str] = None
    top_k: int = 5
    mode: Optional[str] = None  # semantic (defaut) ou simple
