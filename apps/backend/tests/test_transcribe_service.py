import os

import pytest
from app.domain.entities.transcript_segment import TranscriptSegment
from app.infrastructure.ai.openai_transcription_provider import (
    OpenAITranscriptionProvider,
)
from app.services.in_memory_session_repo import InMemorySegmentRepository
from app.services.transcribe_segment_service import TranscribeSegmentService


@pytest.mark.skipif(
    not os.getenv("NC_OPENAI_API_KEY") or not os.getenv("NC_TEST_AUDIO_FILE"),
    reason="Requires NC_OPENAI_API_KEY and NC_TEST_AUDIO_FILE to run integration test",
)
def test_transcribe_segment_returns_segment_with_text():
    provider = OpenAITranscriptionProvider()
    segments = InMemorySegmentRepository()
    service = TranscribeSegmentService(provider=provider, segments=segments)

    seg = TranscriptSegment(
        id="t1",
        session_id="s1",
        start_ms=0,
        end_ms=1000,
        text="stub",
        speaker_label=None,
    )
    with open(os.environ["NC_TEST_AUDIO_FILE"], "rb") as f:
        audio_bytes = f.read()
    out = service.transcribe_segment(seg, audio_bytes)

    assert isinstance(out.text, str)
    assert len(out.text) > 0
    assert out.text != "stub"
    assert out.session_id == seg.session_id
