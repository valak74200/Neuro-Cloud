from abc import ABC, abstractmethod
from typing import List

from app.domain.entities.action_item import ActionItem


class ActionItemsProvider(ABC):
    """Port pour extraire des items d'action à partir d'un transcript."""

    @abstractmethod
    def extract(self, transcript: str) -> List[ActionItem]:
        raise NotImplementedError
