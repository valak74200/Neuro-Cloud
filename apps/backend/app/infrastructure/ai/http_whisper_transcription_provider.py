import os
from typing import Optional

import httpx
from app.domain.providers.transcription_provider import TranscriptionProvider


class HttpWhisperTranscriptionProvider(TranscriptionProvider):
    """HTTP adapter for a faster-whisper server exposing a simple REST API.

    Expected server contract (typical implementations):
      POST {base_url}/transcribe
        - multipart/form-data: file (audio), optional 'language'
        - returns JSON: { "text": "..." }
    """

    def __init__(
        self, base_url: Optional[str] = None, api_key: Optional[str] = None
    ) -> None:
        self._base_url = base_url or os.getenv("NC_WHISPER_URL")
        if not self._base_url:
            raise RuntimeError("NC_WHISPER_URL is required")
        self._api_key = api_key or os.getenv("NC_WHISPER_API_KEY")
        # Allow compatibility with popular servers (e.g., /asr endpoint)
        self._path = os.getenv("NC_WHISPER_PATH", "/transcribe")

    def transcribe(self, audio: bytes, language: Optional[str] = None) -> str:
        headers = {}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        path = self._path if self._path.startswith("/") else f"/{self._path}"
        url = f"{self._base_url.rstrip('/')}{path}"

        # Default contract: /transcribe with 'file'
        files_key = "file"
        data: dict[str, str] = {}

        # Compatibility: /asr (e.g., onerahmet/whisper-asr-webservice)
        if path.endswith("/asr"):
            files_key = "audio_file"
            data["task"] = "transcribe"
            if language:
                data["language"] = language
        else:
            if language:
                data["language"] = language

        files = {files_key: ("audio.wav", audio, "audio/wav")}

        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, files=files, data=data)
            resp.raise_for_status()
            j = resp.json()
            # Try common keys
            if "text" in j and isinstance(j["text"], str):
                return j["text"]
            # Some servers return segments; join them
            if "segments" in j and isinstance(j["segments"], list):
                try:
                    return " ".join(seg.get("text", "") for seg in j["segments"]) or ""
                except Exception:
                    return ""
            return ""
