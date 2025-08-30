import pytest
from app.domain.entities.recall_card import RecallCard
from app.domain.entities.tag import ImportanceScore, Tag


def test_recall_card_valid():
    card = RecallCard(
        id="r1",
        user_id="u1",
        title="Résumé réunion",
        summary="Décisions et actions",
        tags=[Tag("meeting"), Tag("project")],
        importance=ImportanceScore(0.7),
    )
    assert card.title


def test_recall_card_requires_fields():
    with pytest.raises(ValueError):
        RecallCard(
            id="x",
            user_id="",
            title="t",
            summary="s",
            tags=[],
            importance=ImportanceScore(0.3),
        )
    with pytest.raises(ValueError):
        RecallCard(
            id="x",
            user_id="u",
            title="",
            summary="s",
            tags=[],
            importance=ImportanceScore(0.3),
        )
