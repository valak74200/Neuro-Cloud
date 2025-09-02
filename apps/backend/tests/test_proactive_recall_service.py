from datetime import datetime, timedelta

from app.domain.entities.recall_card import RecallCard
from app.domain.entities.tag import ImportanceScore, Tag
from app.services.proactive_recall_service import ProactiveRecallService


def mk_card(i: int, score: float) -> RecallCard:
    return RecallCard(
        id=f"c{i}",
        user_id="u",
        title=f"Card {i}",
        summary="Résumé",
        tags=[Tag("a")],
        importance=ImportanceScore(score),
    )


def test_proactive_recall_selects_high_importance() -> None:
    svc = ProactiveRecallService()
    cards = [mk_card(1, 0.2), mk_card(2, 0.6), mk_card(3, 0.8)]
    last = {}
    res = svc.select(cards, last)
    assert [c.id for c in res] == ["c3", "c2"]


def test_proactive_recall_respects_cooldown() -> None:
    svc = ProactiveRecallService()
    cards = [mk_card(1, 0.9), mk_card(2, 0.9)]
    now = datetime.utcnow()
    last = {"c1": now - timedelta(hours=1)}  # encore en cooldown
    res = svc.select(cards, last)
    assert [c.id for c in res] == ["c2"]
