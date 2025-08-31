import pytest
from app.domain.entities.capture_session import CaptureSession
from app.services.in_memory_session_repo import InMemorySessionRepository
from app.services.session_service import SessionService


def test_start_session_creates_and_persists_session():
    repo = InMemorySessionRepository()
    svc = SessionService(session_repository=repo)

    sess = svc.start_session(user_id="u1", session_type="meeting", started_at_ms=10)

    assert isinstance(sess, CaptureSession)
    assert repo.get(sess.id) is not None
    listed = repo.list_by_user("u1")
    assert any(s.id == sess.id for s in listed)


def test_end_session_updates_existing():
    repo = InMemorySessionRepository()
    svc = SessionService(session_repository=repo)

    sess = svc.start_session(user_id="u1", session_type="meeting", started_at_ms=10)
    ended = svc.end_session(session_id=sess.id, ended_at_ms=20)

    assert ended.ended_at_ms == 20


def test_end_session_raises_if_not_found():
    repo = InMemorySessionRepository()
    svc = SessionService(session_repository=repo)

    with pytest.raises(ValueError):
        svc.end_session(session_id="missing", ended_at_ms=10)
