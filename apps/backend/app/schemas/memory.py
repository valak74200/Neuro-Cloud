from typing import Literal, Optional

from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    """Requête de création d'un souvenir."""

    # Optional en auth (user issu du token)
    user_id: Optional[str] = Field(
        default=None, description="Identifiant utilisateur (ignoré si authentifié)"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Contenu textuel du souvenir",
        examples=["Note rapide"],
    )
    source: Literal[
        "manual",
        "hotword",
        "meeting",
        "course",
        "call",
    ] = Field(
        default="manual",
        description="Source d'acquisition du souvenir",
        examples=["manual"],
    )


class MemoryResponse(BaseModel):
    """Réponse représentant un souvenir."""

    id: str = Field(description="Identifiant du souvenir", examples=["mem_123"])
    user_id: str = Field(description="Propriétaire du souvenir", examples=["user_123"])
    content: str = Field(description="Contenu textuel")
    source: str = Field(description="Source (manual, meeting, ...)")
