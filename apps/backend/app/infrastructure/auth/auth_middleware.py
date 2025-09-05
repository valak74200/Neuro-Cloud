from typing import Optional

from app.domain.entities.user import User
from app.infrastructure.auth.supabase_auth_provider import SupabaseAuthProvider
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Global auth provider instance
_auth_provider: Optional[SupabaseAuthProvider] = None


def get_auth_provider() -> SupabaseAuthProvider:
    """Get or create the global auth provider instance."""
    global _auth_provider
    if _auth_provider is None:
        _auth_provider = SupabaseAuthProvider()
    return _auth_provider


# FastAPI security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_provider: SupabaseAuthProvider = Depends(get_auth_provider),
) -> User:
    """Dependency to get the current authenticated user.

    Extracts and validates JWT token from Authorization header,
    then returns the authenticated user.

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Verify the JWT token
        claims = auth_provider.verify_token(token)

        # Get or create user from claims
        user = auth_provider.get_user_by_id(claims.user_id)
        if not user:
            user = auth_provider.create_or_update_user(claims)

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_provider: SupabaseAuthProvider = Depends(get_auth_provider),
) -> Optional[User]:
    """Optional authentication dependency.

    Returns the authenticated user if token is provided and valid,
    otherwise returns None.

    This is useful for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    token = credentials.credentials

    try:
        claims = auth_provider.verify_token(token)
        user = auth_provider.get_user_by_id(claims.user_id)
        if not user:
            user = auth_provider.create_or_update_user(claims)
        return user

    except Exception:
        # Return None for any auth failure when optional
        return None


def require_auth(user: User = Depends(get_current_user)) -> User:
    """Simple dependency that just requires authentication.

    Use this when you only need to ensure the user is authenticated
    but don't need the user object itself.
    """
    return user


# Middleware for adding auth context to request
async def auth_middleware(request: Request, call_next):
    """Middleware to add authentication context to request.

    This middleware can be used to add auth information to request.state
    for use in downstream handlers.
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        request.state.token = token

        # Optionally verify token and add user to request state
        try:
            auth_provider = get_auth_provider()
            claims = auth_provider.verify_token(token)
            request.state.user_claims = claims

            user = auth_provider.get_user_by_id(claims.user_id)
            if not user:
                user = auth_provider.create_or_update_user(claims)
            request.state.user = user
        except Exception:
            # Don't fail the request, just don't add user info
            pass

    response = await call_next(request)
    return response
