import os

import pytest
from app.infrastructure.ai.http_whisper_transcription_provider import (
    HttpWhisperTranscriptionProvider,
)


@pytest.mark.skipif(not os.getenv("NC_WHISPER_URL"), reason="NC_WHISPER_URL not set")
def test_http_whisper_transcription_returns_text():
    provider = HttpWhisperTranscriptionProvider()
    # tiny fake wav header; in real integration, use a small sample
    audio = b"RIFF....WAVEfmt "
    text = provider.transcribe(audio, language="fr")
    assert isinstance(text, str)
    # Empty string acceptable if server returns no text for tiny input
    assert text is not None
