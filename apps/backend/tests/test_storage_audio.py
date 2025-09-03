import os
import uuid

import httpx
import pytest
from app.infrastructure.storage.s3_storage import S3AudioStorage


def _minio_reachable() -> bool:
    url = os.getenv("NC_S3_ENDPOINT")
    if not url:
        return False
    try:
        with httpx.Client(timeout=1.0) as client:
            resp = client.get(url.rstrip("/") + "/minio/health/ready")
            return resp.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not _minio_reachable(), reason="MinIO/S3 not reachable")
def test_storage_audio_put_get_delete_roundtrip():
    storage = S3AudioStorage()
    key = f"test-audio-{uuid.uuid4()}.wav"
    content = b"RIFF....WAVEfmt "  # minimal header bytes for test

    storage.put(key, content, content_type="audio/wav")
    out = storage.get(key)
    assert out == content

    storage.delete(key)
    # After delete, get should raise; we assert by attempting and catching
    with pytest.raises(Exception):
        storage.get(key)
