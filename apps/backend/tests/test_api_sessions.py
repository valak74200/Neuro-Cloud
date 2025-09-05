import os
from datetime import datetime, timedelta

import jwt
from app.main import create_app
from fastapi.testclient import TestClient


def _token(uid: str) -> str:
    os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
    now = datetime.utcnow()
    return jwt.encode(
        {
            "sub": uid,
            "email": f"{uid}@example.com",
            "role": "authenticated",
            "aud": "authenticated",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        os.environ["SUPABASE_JWT_SECRET"],
        algorithm="HS256",
    )


def test_sessions_flow():
    app = create_app()
    client = TestClient(app)
    t = _token("user-sess")

    # Start session
    r = client.post(
        "/api/v1/sessions",
        json={"type": "personal", "started_at_ms": 1},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    sid = r.json()["id"]

    # List sessions
    r2 = client.get("/api/v1/sessions", headers={"Authorization": f"Bearer {t}"})
    assert r2.status_code == 200
    assert any(s["id"] == sid for s in r2.json())

    # End session
    r3 = client.post(
        f"/api/v1/sessions/{sid}/end",
        json={"ended_at_ms": 2},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r3.status_code == 200
    assert r3.json()["ended_at_ms"] == 2
