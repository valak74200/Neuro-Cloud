import pytest
from app.domain.entities.tag import ImportanceScore, Tag


def test_tag_and_importance_valid():
    t = Tag(value="meeting")
    s = ImportanceScore(score=0.8)
    assert t.value == "meeting"
    assert s.score == 0.8


def test_tag_importance_validations():
    with pytest.raises(ValueError):
        Tag(value="")
    with pytest.raises(ValueError):
        ImportanceScore(score=-0.1)
    with pytest.raises(ValueError):
        ImportanceScore(score=1.1)
