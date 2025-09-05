from typing import Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Response model for user information."""

    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True
