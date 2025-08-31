from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ActionItem:
    id: str
    description: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None  # ISO date string optionnelle

    def __post_init__(self) -> None:
        if not self.description:
            raise ValueError("description is required")
