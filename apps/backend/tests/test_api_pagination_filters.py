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


def test_pagination_and_filters_memories_sessions_segments_search():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-page")

    # Create memories with sources
    for content, source in [
        ("alpha", "manual"),
        ("beta", "meeting"),
        ("alphabet", "manual"),
    ]:
        r = client.post(
            "/api/v1/memories",
            json={"content": content, "source": source},
            headers={"Authorization": f"Bearer {t}"},
        )
        assert r.status_code == 200

    # Pagination memories
    r = client.get(
        "/api/v1/memories",
        params={
            "limit": 2,
            "offset": 0,
            "q": "alpha",
            "source": "manual",
            "sort": "content",
        },
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data) <= 2
    assert all("alpha" in m["content"] for m in data)

    # Sessions + segments
    r = client.post(
        "/api/v1/sessions",
        json={"type": "personal", "started_at_ms": 1},
        headers={"Authorization": f"Bearer {t}"},
    )
    sid = r.json()["id"]
    client.post(
        "/api/v1/segments",
        json={"session_id": sid, "start_ms": 0, "end_ms": 1, "text": "hello"},
        headers={"Authorization": f"Bearer {t}"},
    )
    client.post(
        "/api/v1/segments",
        json={"session_id": sid, "start_ms": 1, "end_ms": 2, "text": "world"},
        headers={"Authorization": f"Bearer {t}"},
    )

    r2 = client.get(
        f"/api/v1/sessions/{sid}/segments",
        params={"limit": 1, "offset": 1, "q": "o"},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    # Search filter by session
    r3 = client.get(
        "/api/v1/search",
        params={"q": "hello", "top_k": 5, "session_id": sid},
    )
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)
