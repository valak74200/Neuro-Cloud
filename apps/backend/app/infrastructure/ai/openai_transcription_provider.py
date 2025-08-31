import os
from typing import Optional

import httpx
from app.domain.providers.transcription_provider import TranscriptionProvider


class OpenAITranscriptionProvider(TranscriptionProvider):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "whisper-1",
        base_url: Optional[str] = None,
    ) -> None:
        self._api_key = api_key or os.getenv("NC_OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("NC_OPENAI_API_KEY is required")
        self._model = model
        self._base_url = base_url or os.getenv(
            "NC_OPENAI_BASE_URL", "https://api.openai.com/v1"
        )

    def transcribe(self, audio: bytes, language: Optional[str] = None) -> str:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
        }
        # Using multipart/form-data per OpenAI API
        files = {"file": ("audio.wav", audio, "audio/wav")}
        data = {"model": self._model}
        if language:
            data["language"] = language
        url = f"{self._base_url}/audio/transcriptions"
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            j = resp.json()
            # OpenAI returns {'text': '...'}
            return j.get("text", "")
