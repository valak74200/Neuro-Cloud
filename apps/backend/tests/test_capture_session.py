import pytest
from app.domain.entities.capture_session import CaptureSession


def test_capture_session_valid():
    s = CaptureSession(id="c1", user_id="u1", type="meeting", started_at_ms=10)
    assert s.id == "c1"
    assert s.type == "meeting"


def test_capture_session_invalid_user_or_time():
    with pytest.raises(ValueError):
        CaptureSession(id="x", user_id="", type="meeting", started_at_ms=0)
    with pytest.raises(ValueError):
        CaptureSession(id="x", user_id="u", type="meeting", started_at_ms=-1)


def test_capture_session_end_must_be_after_start():
    with pytest.raises(ValueError):
        CaptureSession(
            id="x",
            user_id="u",
            type="meeting",
            started_at_ms=100,
            ended_at_ms=50,
        )
