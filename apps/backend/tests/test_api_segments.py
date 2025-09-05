import os
from datetime import datetime, timedelta

import jwt
from app.main import create_app
from fastapi.testclient import TestClient


def _tok(uid: str) -> str:
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


def test_segments_flow():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-seg")

    # Start a session
    r = client.post(
        "/api/v1/sessions",
        json={"type": "personal", "started_at_ms": 1},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    sid = r.json()["id"]

    # Create a segment
    r2 = client.post(
        "/api/v1/segments",
        json={
            "session_id": sid,
            "start_ms": 0,
            "end_ms": 1000,
            "text": "hello",
        },
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r2.status_code == 200
    seg_id = r2.json()["id"]

    # List segments
    r3 = client.get(
        f"/api/v1/sessions/{sid}/segments",
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r3.status_code == 200
    assert any(s["id"] == seg_id for s in r3.json())
