import uuid
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class User:
    """Domain entity representing a user."""

    id: str
    email: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None

    @staticmethod
    def create(
        email: str,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> "User":
        """Create a new User entity."""
        if not email or not email.strip():
            raise ValueError("Email is required")

        # Validate email format (basic validation)
        if "@" not in email or "." not in email:
            raise ValueError("Invalid email format")

        return User(
            id=user_id or str(uuid.uuid4()),
            email=email.strip().lower(),
            name=name.strip() if name else None,
            avatar_url=avatar_url.strip() if avatar_url else None,
        )

    def update_profile(
        self, name: Optional[str] = None, avatar_url: Optional[str] = None
    ) -> "User":
        """Create a new User with updated profile information."""
        return User(
            id=self.id,
            email=self.email,
            name=name.strip() if name else self.name,
            avatar_url=avatar_url.strip() if avatar_url else self.avatar_url,
        )


@dataclass(frozen=True)
class UserClaims:
    """JWT claims extracted from Supabase token."""

    user_id: str
    email: str
    role: Optional[str] = None
    exp: Optional[int] = None

    @staticmethod
    def from_dict(claims: dict) -> "UserClaims":
        """Create UserClaims from JWT payload dictionary."""
        return UserClaims(
            user_id=claims.get("sub", ""),
            email=claims.get("email", ""),
            role=claims.get("role"),
            exp=claims.get("exp"),
        )
