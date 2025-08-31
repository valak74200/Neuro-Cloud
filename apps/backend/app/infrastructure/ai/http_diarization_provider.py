import os
from typing import List, Optional

import httpx
from app.domain.entities.diarization_segment import DiarizationSegment
from app.domain.providers.diarization_provider import DiarizationProvider


class HttpDiarizationProvider(DiarizationProvider):
    def __init__(
        self, base_url: Optional[str] = None, api_key: Optional[str] = None
    ) -> None:
        self._base_url = base_url or os.getenv("NC_DIARIZATION_URL")
        if not self._base_url:
            raise RuntimeError("NC_DIARIZATION_URL is required")
        self._api_key = api_key or os.getenv("NC_DIARIZATION_API_KEY")

    def diarize(
        self, audio: bytes, language: Optional[str] = None
    ) -> List[DiarizationSegment]:
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data = {}
        if language:
            data["language"] = language
        url = f"{self._base_url.rstrip('/')}/diarize"
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            payload = resp.json()
        segments = []
        for item in payload.get("segments", []):
            segments.append(
                DiarizationSegment(
                    start_ms=int(item["start_ms"]),
                    end_ms=int(item["end_ms"]),
                    speaker_label=str(
                        item.get("speaker") or item.get("speaker_label") or "SPEAKER"
                    ),
                )
            )
        return segments
