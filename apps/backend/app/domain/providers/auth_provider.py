from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.user import User, UserClaims


class AuthProvider(ABC):
    """Port for authentication services."""

    @abstractmethod
    def verify_token(self, token: str) -> UserClaims:
        """Verify JWT token and return user claims.

        Args:
            token: JWT token to verify

        Returns:
            UserClaims: Extracted claims from the token

        Raises:
            ValueError: If token is invalid or expired
        """
        raise NotImplementedError

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    def create_or_update_user(self, claims: UserClaims) -> User:
        """Create or update user from JWT claims.

        Args:
            claims: JWT claims from verified token

        Returns:
            User: Created or updated user entity
        """
        raise NotImplementedError
