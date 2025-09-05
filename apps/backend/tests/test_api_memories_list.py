import os
from datetime import datetime, timedelta

import jwt
from app.main import create_app
from fastapi.testclient import TestClient


def _make_token(user_id: str, email: str) -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "test-secret")
    now = datetime.utcnow()
    return jwt.encode(
        {
            "sub": user_id,
            "email": email,
            "role": "authenticated",
            "aud": "authenticated",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )


def test_list_memories_requires_auth():
    app = create_app()
    client = TestClient(app)
    res = client.get("/api/v1/memories")
    assert res.status_code == 401


def test_list_memories_returns_items():
    os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
    token = _make_token("user-xyz", "u@example.com")

    app = create_app()
    client = TestClient(app)

    # Create two memories
    for content in ("A", "B"):
        r = client.post(
            "/api/v1/memories",
            json={"content": content, "source": "manual"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200

    # List memories
    r = client.get(
        "/api/v1/memories",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert {item["content"] for item in data} >= {"A", "B"}
