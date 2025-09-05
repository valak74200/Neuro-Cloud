import os
from datetime import datetime, timedelta

import jwt
from app.main import create_app
from fastapi.testclient import TestClient


def test_create_memory_endpoint_returns_created_memory():
    app = create_app()
    client = TestClient(app)

    secret = os.environ.get("SUPABASE_JWT_SECRET", "test-secret")
    now = datetime.utcnow()
    token = jwt.encode(
        {
            "sub": "u1",
            "email": "u1@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        secret,
        algorithm="HS256",
    )

    payload = {"user_id": "ignored", "content": "hello world", "source": "manual"}
    res = client.post(
        "/api/v1/memories", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"]
    assert data["user_id"] == "u1"
    assert data["content"] == "hello world"
    assert data["source"] == "manual"
