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


def test_recall_feed_empty():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-recall")
    r = client.get("/api/v1/recall/feed", headers={"Authorization": f"Bearer {t}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
