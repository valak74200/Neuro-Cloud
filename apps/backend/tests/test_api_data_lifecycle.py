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


def test_export_and_purge_flow():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-dl")

    # Create two memories
    for content in ("X", "Y"):
        r = client.post(
            "/api/v1/memories",
            json={"content": content, "source": "manual"},
            headers={"Authorization": f"Bearer {t}"},
        )
        assert r.status_code == 200

    # Export
    r2 = client.get("/api/v1/export", headers={"Authorization": f"Bearer {t}"})
    assert r2.status_code == 200
    data = r2.json()
    assert len(data["items"]) >= 2

    # Purge
    r3 = client.post(
        "/api/v1/purge",
        json={"confirm": True},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r3.status_code == 200
    assert r3.json()["deleted"] >= 2
