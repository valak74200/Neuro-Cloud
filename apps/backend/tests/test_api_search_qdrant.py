import os
from datetime import datetime, timedelta

import jwt
import pytest
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


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("NC_VECTORDB_URL"), reason="Requires a running Qdrant instance"
)
def test_search_qdrant_live():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-qdrant")

    # Crée une session + un segment indexé
    r = client.post(
        "/api/v1/sessions",
        json={"type": "personal", "started_at_ms": 1},
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    sid = r.json()["id"]

    client.post(
        "/api/v1/segments",
        json={"session_id": sid, "start_ms": 0, "end_ms": 1, "text": "bonjour qdrant"},
        headers={"Authorization": f"Bearer {t}"},
    )

    # Recherche live via Qdrant (provider embeddings requis)
    res = client.get(
        "/api/v1/search", params={"q": "bonjour", "top_k": 3, "session_id": sid}
    )
    assert res.status_code == 200
    # Résultats possibles (>=0) selon embeddings clés
    assert isinstance(res.json(), list)
