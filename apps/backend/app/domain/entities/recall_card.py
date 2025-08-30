from dataclasses import dataclass
from typing import List

from app.domain.entities.tag import ImportanceScore, Tag


@dataclass(frozen=True)
class RecallCard:
    id: str
    user_id: str
    title: str
    summary: str
    tags: List[Tag]
    importance: ImportanceScore

    def __post_init__(self) -> None:
        if not self.user_id or not self.title or not self.summary:
            raise ValueError("user_id, title and summary are required")
