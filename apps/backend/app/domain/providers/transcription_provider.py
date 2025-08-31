from typing import Optional, Protocol


class TranscriptionProvider(Protocol):
    def transcribe(self, audio: bytes, language: Optional[str] = None) -> str: ...
