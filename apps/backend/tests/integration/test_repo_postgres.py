import os
from contextlib import contextmanager
from typing import Generator

import pytest
from app.domain.entities.memory import Memory
from app.infrastructure.db.postgres import get_session_factory
from app.infrastructure.repositories.postgres_memory_repository import (
    PostgresMemoryRepository,
)
from sqlalchemy.orm import Session


@contextmanager
def session_scope() -> "Generator[Session, None, None]":
    SessionFactory = get_session_factory()
    session = SessionFactory()
    try:
        yield session
    finally:
        session.close()


@pytest.mark.integration
def test_postgres_memory_repository_save_and_list_by_user():
    if not os.getenv("NC_PG_DSN"):
        pytest.skip("NC_PG_DSN not configured")

    user_id = "user-int-1"
    mem = Memory.create(user_id=user_id, content="bonjour", source="manual")

    with session_scope() as s:
        repo = PostgresMemoryRepository(s)
        saved = repo.save(mem)
        assert saved.id == mem.id

    with session_scope() as s:
        repo = PostgresMemoryRepository(s)
        items = repo.list_by_user(user_id)
        assert any(m.id == mem.id for m in items)
