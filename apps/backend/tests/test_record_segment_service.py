import pytest
from app.domain.entities.capture_session import CaptureSession
from app.services.in_memory_session_repo import (
    InMemorySegmentRepository,
    InMemorySessionRepository,
)
from app.services.record_segment_service import RecordSegmentService


def test_record_segment_success():
    sess_repo = InMemorySessionRepository()
    seg_repo = InMemorySegmentRepository()
    service = RecordSegmentService(session_repo=sess_repo, segment_repo=seg_repo)

    sess = sess_repo.save(
        CaptureSession(id="s1", user_id="u1", type="meeting", started_at_ms=0)
    )
    seg = service.record_segment(sess.id, 0, 1000, "hello", "A")
    assert seg.session_id == sess.id
    assert len(seg_repo.list_by_session(sess.id)) == 1


def test_record_segment_session_not_found():
    sess_repo = InMemorySessionRepository()
    seg_repo = InMemorySegmentRepository()
    service = RecordSegmentService(session_repo=sess_repo, segment_repo=seg_repo)

    with pytest.raises(ValueError):
        service.record_segment("missing", 0, 1000, "hello")
