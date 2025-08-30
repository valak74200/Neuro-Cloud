import pytest
from app.domain.entities.participant import Participant


def test_participant_valid():
    p = Participant(id="p1", display_name="Alice")
    assert p.id == "p1"
    assert p.display_name == "Alice"


def test_participant_requires_fields():
    with pytest.raises(ValueError):
        Participant(id="", display_name="x")
    with pytest.raises(ValueError):
        Participant(id="x", display_name="")
