import io
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


def test_upload_segment_validates_and_stores(monkeypatch):
    app = create_app()
    client = TestClient(app)
    t = _tok("user-up")

    # Stub S3 storage put to avoid real network
    from app.infrastructure.storage import s3_storage

    calls = {}

    def fake_put(self, key: str, data: bytes, content_type: str = "audio/wav"):
        calls["key"] = key
        calls["data"] = data
        calls["content_type"] = content_type

    monkeypatch.setattr(s3_storage.S3AudioStorage, "put", fake_put)

    # Small WAV payload
    wav_bytes = b"RIFF0000WAVEfmt "
    files = {"file": ("sample.wav", io.BytesIO(wav_bytes), "audio/wav")}
    data = {"session_id": "sess-1"}
    r = client.post(
        "/api/v1/segments/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "key" in body and body["size_bytes"] == len(wav_bytes)
    assert calls.get("content_type") == "audio/wav"


def test_upload_segment_rejects_bad_type():
    app = create_app()
    client = TestClient(app)
    t = _tok("user-up2")

    files = {"file": ("sample.txt", io.BytesIO(b"hello"), "text/plain")}
    data = {"session_id": "sess-1"}
    r = client.post(
        "/api/v1/segments/upload",
        files=files,
        data=data,
        headers={"Authorization": f"Bearer {t}"},
    )
    assert r.status_code == 415
