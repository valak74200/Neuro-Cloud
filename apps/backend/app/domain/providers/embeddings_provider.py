from abc import ABC, abstractmethod
from typing import List


class EmbeddingsProvider(ABC):
    """Port pour générer des embeddings à partir de texte."""

    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Retourne une liste de vecteurs (un par texte)."""
        raise NotImplementedError
