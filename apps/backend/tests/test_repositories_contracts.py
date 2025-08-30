from typing import Protocol

from app.domain.repositories.session_repository import (
    RecallCardRepository,
    SegmentRepository,
    SessionRepository,
)


def test_session_repository_protocol_methods():
    assert issubclass(SessionRepository, Protocol)
    for name in ("save", "get", "list_by_user"):
        assert hasattr(SessionRepository, name)


def test_segment_repository_protocol_methods():
    assert issubclass(SegmentRepository, Protocol)
    for name in ("save", "list_by_session"):
        assert hasattr(SegmentRepository, name)


def test_recall_card_repository_protocol_methods():
    assert issubclass(RecallCardRepository, Protocol)
    for name in ("save", "list_by_user"):
        assert hasattr(RecallCardRepository, name)
