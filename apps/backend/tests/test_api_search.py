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


def test_search_returns_results():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-search")

    # Créer une session et un segment indexé
    r = client.post(
        "/api/v1/sessions",
        json={"type": "personal", "started_at_ms": 1},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    sid = r.json()["id"]

    r2 = client.post(
        "/api/v1/segments",
        json={"session_id": sid, "start_ms": 0, "end_ms": 1000, "text": "bonjour"},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r2.status_code == 200

    # Rechercher
    r3 = client.get("/api/v1/search", params={"q": "bonjour", "top_k": 3})
    assert r3.status_code == 200
    data = r3.json()
    assert isinstance(data, list)
    assert len(data) >= 1
