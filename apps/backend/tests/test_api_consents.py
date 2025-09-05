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


def test_consents_flow():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-consent")

    # Start a session
    r = client.post(
        "/api/v1/sessions",
        json={"type": "personal", "started_at_ms": 1},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    sid = r.json()["id"]

    # Create consent
    r2 = client.post(
        "/api/v1/consents",
        json={
            "session_id": sid,
            "participant_id": "p1",
            "method": "in_app",
            "granted": True,
            "timestamp_ms": 2,
        },
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r2.status_code == 200
    cid = r2.json()["id"]

    # List consents
    r3 = client.get(
        "/api/v1/consents",
        params={"session_id": sid},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r3.status_code == 200
    data = r3.json()
    assert any(c["id"] == cid for c in data)
