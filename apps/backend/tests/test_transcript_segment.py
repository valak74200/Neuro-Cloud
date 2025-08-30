import pytest
from app.domain.entities.transcript_segment import TranscriptSegment


def test_transcript_segment_valid():
    seg = TranscriptSegment(
        id="s1",
        session_id="sess1",
        start_ms=0,
        end_ms=1200,
        text="Bonjour",
        speaker_label="A",
    )
    assert seg.id == "s1"
    assert seg.text == "Bonjour"


def test_transcript_segment_invalid_times():
    with pytest.raises(ValueError):
        TranscriptSegment(
            id="x",
            session_id="s",
            start_ms=-1,
            end_ms=0,
            text="hi",
        )
    with pytest.raises(ValueError):
        TranscriptSegment(
            id="x",
            session_id="s",
            start_ms=100,
            end_ms=50,
            text="hi",
        )


def test_transcript_segment_requires_text():
    with pytest.raises(ValueError):
        TranscriptSegment(
            id="x",
            session_id="s",
            start_ms=0,
            end_ms=1,
            text="",
        )
