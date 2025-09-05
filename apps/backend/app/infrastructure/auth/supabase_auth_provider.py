import os
from typing import Optional

import httpx
import jwt
from app.domain.entities.user import User, UserClaims
from app.domain.providers.auth_provider import AuthProvider
from jwt import PyJWKClient


class SupabaseAuthProvider(AuthProvider):
    """Supabase authentication provider for JWT validation and user management."""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_jwt_secret: Optional[str] = None,
    ) -> None:
        self._supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self._supabase_jwt_secret = supabase_jwt_secret or os.getenv(
            "SUPABASE_JWT_SECRET"
        )

        # JWKS endpoint for RS* algorithms (Supabase):
        # https://<project>.supabase.co/auth/v1/certs
        self._jwks_url = f"{self._supabase_url}/auth/v1/certs"

        # Cache for public key (rarely used now that PyJWKClient is available)
        self._public_key: Optional[str] = None

    def _get_public_key(self) -> str:
        """Fetch Supabase public key for JWT verification."""
        if self._public_key:
            return self._public_key

        # Supabase JWKS endpoint (certs)
        jwks_url = self._jwks_url

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(jwks_url)
                response.raise_for_status()
                jwks = response.json()

                # Get the first key (usually there's only one)
                if not jwks.get("keys"):
                    raise ValueError("No keys found in JWKS")

                key_data = jwks["keys"][0]
                n = key_data.get("n")
                e = key_data.get("e", "AQAB")  # Default exponent

                if not n:
                    raise ValueError("No modulus found in JWKS key")

                # Construct RSA public key
                import base64

                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import serialization
                from cryptography.hazmat.primitives.asymmetric import rsa

                # Decode base64url
                n_bytes = base64.urlsafe_b64decode(n + "=" * (4 - len(n) % 4))
                e_bytes = base64.urlsafe_b64decode(e + "=" * (4 - len(e) % 4))

                # Convert to integers
                n_int = int.from_bytes(n_bytes, byteorder="big")
                e_int = int.from_bytes(e_bytes, byteorder="big")

                # Create public key
                public_key = rsa.RSAPublicNumbers(e_int, n_int).public_key(
                    default_backend()
                )
                self._public_key = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                ).decode()

                return self._public_key

        except Exception as exc:
            raise RuntimeError(f"Failed to fetch Supabase public key: {exc}")

    def verify_token(self, token: str) -> UserClaims:
        """Verify JWT token (HS256 or RS*) and extract user claims."""
        if not token or not token.strip():
            raise ValueError("Token is required")

        try:
            # Detect algorithm from header
            header = jwt.get_unverified_header(token)
            alg = (header.get("alg") or "").upper()

            if alg.startswith("HS"):
                # HS256: verify with SUPABASE_JWT_SECRET directly
                secret = self._supabase_jwt_secret
                if not secret:
                    raise ValueError("SUPABASE_JWT_SECRET is required for HS tokens")
                payload = jwt.decode(
                    token,
                    secret,
                    algorithms=[alg],
                    options={"verify_aud": False},
                )
            elif alg.startswith("RS"):
                # RS*: verify against Supabase JWKS certs
                if not self._supabase_url:
                    raise ValueError("SUPABASE_URL is required for RS tokens")
                jwk_client = PyJWKClient(self._jwks_url)
                signing_key = jwk_client.get_signing_key_from_jwt(token).key
                payload = jwt.decode(
                    token,
                    signing_key,
                    algorithms=[alg],
                    options={"verify_aud": False},
                )
            else:
                # Unknown/unsupported algorithm
                raise ValueError(f"Unsupported JWT algorithm: {alg}")

            # Extract user claims
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("No user ID found in token")

            email = payload.get("email", "")
            role = payload.get("role")

            # Supabase tokens include additional claims
            exp = payload.get("exp")

            return UserClaims(
                user_id=user_id,
                email=email,
                role=role,
                exp=exp,
            )

        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")
        except Exception as e:
            raise ValueError(f"Token verification failed: {e}")

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID from Supabase."""
        # For now, we'll create users on-the-fly from JWT claims.
        # In production, consider caching users or calling a user service.
        return None

    def create_or_update_user(self, claims: UserClaims) -> User:
        """Create or update user from JWT claims."""
        # Extract additional user info from claims if available
        name = (
            claims.__dict__.get("user_metadata", {}).get("name")
            if hasattr(claims, "__dict__")
            else None
        )
        avatar_url = (
            claims.__dict__.get("user_metadata", {}).get("avatar_url")
            if hasattr(claims, "__dict__")
            else None
        )

        return User.create(
            user_id=claims.user_id,
            email=claims.email,
            name=name,
            avatar_url=avatar_url,
        )


# Factory function
def create_supabase_auth_provider() -> SupabaseAuthProvider:
    """Create Supabase auth provider with default configuration."""
    return SupabaseAuthProvider()
