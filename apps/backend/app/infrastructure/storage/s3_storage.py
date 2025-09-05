from __future__ import annotations

import io
import os
from typing import Optional

from minio import Minio


class S3AudioStorage:
    """Minimal S3/MinIO storage adapter for audio blobs.

    Reads configuration from environment by default:
      - NC_S3_ENDPOINT (e.g., http://localhost:9000)
      - NC_S3_ACCESS_KEY_ID
      - NC_S3_SECRET_ACCESS_KEY
      - NC_S3_BUCKET
      - NC_S3_REGION (optional)

    Uses the MinIO Python client (S3-compatible).
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
        secure: Optional[bool] = None,
    ) -> None:
        self._endpoint = (
            endpoint or os.getenv("NC_S3_ENDPOINT") or "http://localhost:9000"
        )
        self._access_key = access_key or os.getenv("NC_S3_ACCESS_KEY_ID")
        self._secret_key = secret_key or os.getenv("NC_S3_SECRET_ACCESS_KEY")
        self._bucket = bucket or os.getenv("NC_S3_BUCKET") or "neuro-cloud"
        self._region = region or os.getenv("NC_S3_REGION")
        if secure is None:
            secure = self._endpoint.startswith("https://")
        # Strip scheme for Minio client host
        host = self._endpoint.replace("https://", "").replace("http://", "")
        self._client = Minio(
            host,
            access_key=self._access_key,
            secret_key=self._secret_key,
            secure=secure,
            region=self._region,
        )

    def _ensure_bucket(self) -> None:
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket, location=self._region)
        except Exception:
            # En tests, on peut monkeypatcher put/get/delete; ne pas échouer ici
            pass

    def put(self, key: str, data: bytes, content_type: str = "audio/wav") -> None:
        self._ensure_bucket()
        stream = io.BytesIO(data)
        self._client.put_object(
            self._bucket,
            key,
            stream,
            length=len(data),
            content_type=content_type,
        )

    def get(self, key: str) -> bytes:
        self._ensure_bucket()
        response = self._client.get_object(self._bucket, key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete(self, key: str) -> None:
        self._ensure_bucket()
        self._client.remove_object(self._bucket, key)
