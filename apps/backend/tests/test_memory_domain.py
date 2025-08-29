import pytest
from app.domain.entities.memory import Memory


def test_memory_create_generates_id_and_preserves_fields():
    mem = Memory.create(user_id="u1", content="hello", source="manual")
    assert mem.id
    assert mem.user_id == "u1"
    assert mem.content == "hello"
    assert mem.source == "manual"


def test_memory_create_requires_user_and_content():
    with pytest.raises(ValueError):
        Memory.create(user_id="", content="x", source="manual")
    with pytest.raises(ValueError):
        Memory.create(user_id="u", content="", source="manual")
