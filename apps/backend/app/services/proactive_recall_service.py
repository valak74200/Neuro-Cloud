from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, List

from app.domain.entities.recall_card import RecallCard


@dataclass(frozen=True)
class RecallPolicy:
    """Politique: rappeler les cartes importantes, récentes, non rappelées récemment."""

    min_importance: float = 0.4
    max_age_days: int = 30
    cooldown_hours: int = 24


class ProactiveRecallService:
    def __init__(self, policy: RecallPolicy | None = None) -> None:
        self._policy = policy or RecallPolicy()

    def select(
        self,
        cards: Iterable[RecallCard],
        last_recall_at: dict[str, datetime],
    ) -> List[RecallCard]:
        now = datetime.utcnow()
        selected: List[RecallCard] = []
        for c in cards:
            # importance
            if c.importance.score < self._policy.min_importance:
                continue
            # âge: pas de timestamp sur RecallCard; filtrer en amont
            # cooldown depuis dernier rappel
            ts = last_recall_at.get(c.id)
            if ts:
                delta = now - ts
                if delta < timedelta(hours=self._policy.cooldown_hours):
                    continue
            selected.append(c)
        # tri par importance décroissante
        selected.sort(key=lambda x: x.importance.score, reverse=True)
        return selected[:10]
