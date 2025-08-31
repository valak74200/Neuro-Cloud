import os

import pytest
from app.domain.entities.diarization_segment import DiarizationSegment
from app.infrastructure.ai.http_diarization_provider import HttpDiarizationProvider
from app.services.diarize_session_service import DiarizeSessionService


@pytest.mark.skipif(
    not os.getenv("NC_DIARIZATION_URL") or not os.getenv("NC_TEST_AUDIO_FILE"),
    reason="Requires NC_DIARIZATION_URL and NC_TEST_AUDIO_FILE to run integration test",
)
def test_diarize_session_returns_segments():
    provider = HttpDiarizationProvider()
    service = DiarizeSessionService(provider)

    with open(os.environ["NC_TEST_AUDIO_FILE"], "rb") as f:
        audio = f.read()

    segs = service.diarize(audio)
    assert isinstance(segs, list)
    if segs:
        assert isinstance(segs[0], DiarizationSegment)
        assert segs[0].end_ms > segs[0].start_ms
