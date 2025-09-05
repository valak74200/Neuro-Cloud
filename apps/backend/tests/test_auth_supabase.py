import os
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from app.domain.entities.user import User, UserClaims
from app.infrastructure.auth.supabase_auth_provider import SupabaseAuthProvider
from app.main import create_app
from fastapi.testclient import TestClient


class TestUserEntity:
    """Test the User domain entity."""

    def test_user_create_valid(self):
        """Test creating a valid user."""
        user = User.create(
            email="test@example.com",
            name="Test User",
            avatar_url="https://example.com/avatar.jpg",
        )

        assert user.id
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.avatar_url == "https://example.com/avatar.jpg"

    def test_user_create_minimal(self):
        """Test creating a user with minimal information."""
        user = User.create(email="test@example.com")

        assert user.id
        assert user.email == "test@example.com"
        assert user.name is None
        assert user.avatar_url is None

    def test_user_create_invalid_email(self):
        """Test creating a user with invalid email."""
        with pytest.raises(ValueError, match="Invalid email"):
            User.create(email="invalid-email")

        with pytest.raises(ValueError, match="Email is required"):
            User.create(email="")

    def test_user_update_profile(self):
        """Test updating user profile."""
        user = User.create(email="test@example.com", name="Old Name")
        updated = user.update_profile(name="New Name", avatar_url="new-avatar.jpg")

        assert updated.id == user.id
        assert updated.email == user.email
        assert updated.name == "New Name"
        assert updated.avatar_url == "new-avatar.jpg"


class TestUserClaims:
    """Test the UserClaims entity."""

    def test_from_dict(self):
        """Test creating UserClaims from dictionary."""
        claims_dict = {
            "sub": "user-123",
            "email": "test@example.com",
            "role": "user",
            "exp": 1234567890,
        }

        claims = UserClaims.from_dict(claims_dict)

        assert claims.user_id == "user-123"
        assert claims.email == "test@example.com"
        assert claims.role == "user"
        assert claims.exp == 1234567890


class TestSupabaseAuthProvider:
    """Test the Supabase authentication provider."""

    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_JWT_SECRET": "test-secret",
            },
        ):
            provider = SupabaseAuthProvider()
            assert provider._supabase_url == "https://test.supabase.co"
            assert provider._supabase_jwt_secret == "test-secret"

    def test_init_missing_url(self):
        """Test error when Supabase URL is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="SUPABASE_URL is required"):
                SupabaseAuthProvider()

    def test_init_missing_secret(self):
        """Test error when JWT secret is missing."""
        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co"}, clear=True
        ):
            with pytest.raises(RuntimeError, match="SUPABASE_JWT_SECRET is required"):
                SupabaseAuthProvider()

    @pytest.mark.skipif(
        not os.getenv("SUPABASE_JWT_SECRET"), reason="Requires SUPABASE_JWT_SECRET"
    )
    def test_verify_token_success(self):
        """Test successful token verification (no mocks)."""
        import jwt

        secret = os.environ["SUPABASE_JWT_SECRET"]
        now = datetime.utcnow()
        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            secret,
            algorithm="HS256",
        )

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": os.environ.get(
                    "SUPABASE_URL", "https://example.supabase.co"
                )
            },
        ):
            provider = SupabaseAuthProvider()
            claims = provider.verify_token(token)
            assert claims.user_id == "user-123"
            assert claims.email == "test@example.com"

    @pytest.mark.skipif(
        not os.getenv("SUPABASE_JWT_SECRET"), reason="Requires SUPABASE_JWT_SECRET"
    )
    def test_verify_token_expired(self):
        """Test handling of expired tokens (no mocks)."""
        import jwt

        secret = os.environ["SUPABASE_JWT_SECRET"]
        now = datetime.utcnow()
        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "iat": now - timedelta(minutes=10),
                "exp": now - timedelta(minutes=5),
            },
            secret,
            algorithm="HS256",
        )
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": os.environ.get(
                    "SUPABASE_URL", "https://example.supabase.co"
                )
            },
        ):
            provider = SupabaseAuthProvider()
            with pytest.raises(ValueError, match="expired"):
                provider.verify_token(token)

    @pytest.mark.skipif(
        not os.getenv("SUPABASE_JWT_SECRET"), reason="Requires SUPABASE_JWT_SECRET"
    )
    def test_verify_token_invalid(self):
        """Test handling of invalid tokens (bad signature)."""
        import jwt

        wrong_secret = "not-the-right-secret"
        now = datetime.utcnow()
        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            wrong_secret,
            algorithm="HS256",
        )
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": os.environ.get(
                    "SUPABASE_URL", "https://example.supabase.co"
                )
            },
        ):
            provider = SupabaseAuthProvider()
            with pytest.raises(ValueError, match="Invalid"):
                provider.verify_token(token)

    def test_verify_token_missing(self):
        """Test handling of missing tokens."""
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_JWT_SECRET": "test-secret",
            },
        ):
            provider = SupabaseAuthProvider()
            with pytest.raises(ValueError, match="Token is required"):
                provider.verify_token("")

    @pytest.mark.skipif(
        not os.getenv("SUPABASE_JWT_SECRET"), reason="Requires SUPABASE_JWT_SECRET"
    )
    def test_verify_token_missing_user_id(self):
        """Test handling of tokens without user ID (no mocks)."""
        import jwt

        secret = os.environ["SUPABASE_JWT_SECRET"]
        now = datetime.utcnow()
        token = jwt.encode(
            {
                # no sub
                "email": "test@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            secret,
            algorithm="HS256",
        )
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": os.environ.get(
                    "SUPABASE_URL", "https://example.supabase.co"
                )
            },
        ):
            provider = SupabaseAuthProvider()
            with pytest.raises(ValueError, match="No user ID found in token"):
                provider.verify_token(token)

    def test_get_user_by_id(self):
        """Test getting user by ID (returns None for now)."""
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_JWT_SECRET": "test-secret",
            },
        ):
            provider = SupabaseAuthProvider()
            user = provider.get_user_by_id("user-123")
            assert user is None

    @patch("jwt.decode")
    def test_create_or_update_user(self, mock_jwt_decode):
        """Test creating user from claims."""
        mock_jwt_decode.return_value = {"sub": "user-123", "email": "test@example.com"}

        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_JWT_SECRET": "test-secret",
            },
        ):
            provider = SupabaseAuthProvider()
            claims = UserClaims(user_id="user-123", email="test@example.com")
            user = provider.create_or_update_user(claims)

            assert user.id == "user-123"
            assert user.email == "test@example.com"


class TestAuthMiddleware:
    """Test the authentication middleware."""

    def test_get_current_user_missing_token(self):
        """Test that missing token raises HTTP 401 on protected endpoint."""
        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/me")

        assert response.status_code == 401
        assert "Authorization header missing" in response.json()["detail"]

    def test_get_current_user_invalid_token(self):
        """Test that invalid token raises HTTP 401 on protected endpoint."""
        app = create_app()
        client = TestClient(app)

        response = client.get(
            "/api/v1/me", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401
        assert "Invalid authentication" in response.json()["detail"]

    @pytest.mark.skipif(
        not os.getenv("SUPABASE_JWT_SECRET"), reason="Requires SUPABASE_JWT_SECRET"
    )
    def test_get_current_user_success(self):
        """Test successful authentication end-to-end (no mocks)."""
        import jwt

        secret = os.environ["SUPABASE_JWT_SECRET"]
        now = datetime.utcnow()
        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            secret,
            algorithm="HS256",
        )

        app = create_app()
        client = TestClient(app)

        response = client.post(
            "/api/v1/memories",
            json={"content": "test content", "source": "manual"},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "user-123"
        assert data["content"] == "test content"

    @pytest.mark.skipif(
        not os.getenv("SUPABASE_JWT_SECRET"), reason="Requires SUPABASE_JWT_SECRET"
    )
    def test_get_current_user_info(self):
        """Test getting current user information (no mocks)."""
        import jwt

        secret = os.environ["SUPABASE_JWT_SECRET"]
        now = datetime.utcnow()
        token = jwt.encode(
            {
                "sub": "user-123",
                "email": "test@example.com",
                "role": "authenticated",
                "aud": "authenticated",
                "iat": now,
                "exp": now + timedelta(minutes=5),
            },
            secret,
            algorithm="HS256",
        )

        app = create_app()
        client = TestClient(app)

        response = client.get(
            "/api/v1/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200


class TestAuthIntegration:
    """Integration tests for authentication."""

    def test_create_supabase_auth_provider_factory(self):
        """Test the factory function creates provider."""
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": "https://test.supabase.co",
                "SUPABASE_JWT_SECRET": "test-secret",
            },
        ):
            from app.infrastructure.auth.supabase_auth_provider import (
                create_supabase_auth_provider,
            )

            provider = create_supabase_auth_provider()
            assert isinstance(provider, SupabaseAuthProvider)

    def test_auth_middleware_integration(self):
        """Test that auth middleware is properly integrated."""
        app = create_app()
        client = TestClient(app)

        # Test health endpoint (no auth required)
        response = client.get("/healthz")
        assert response.status_code == 200

        # Test protected endpoint without auth
        response = client.get("/api/v1/me")
        assert response.status_code == 401

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("SUPABASE_TEST_JWT"),
        reason="Requires SUPABASE_TEST_JWT in environment for live test",
    )
    def test_verify_token_live_with_jwks(self):
        """Live test: verify a real Supabase JWT against JWKS (no mocks)."""
        token = os.environ["SUPABASE_TEST_JWT"]
        provider = SupabaseAuthProvider()
        claims = provider.verify_token(token)
        assert claims.user_id
        assert "@" in (claims.email or "")

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv("SUPABASE_TEST_JWT"),
        reason="Requires SUPABASE_TEST_JWT in environment for live test",
    )
    def test_me_endpoint_live(self):
        """Live test: call /api/v1/me with a real token and expect 200."""
        app = create_app()
        client = TestClient(app)
        token = os.environ["SUPABASE_TEST_JWT"]
        res = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

        # Test user endpoint without auth
        response = client.get("/api/v1/me")
        assert response.status_code == 401
