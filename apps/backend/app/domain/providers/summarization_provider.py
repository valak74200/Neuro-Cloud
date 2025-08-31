from abc import ABC, abstractmethod
from typing import Optional


class SummarizationProvider(ABC):
    """Port d'abstraction pour un fournisseur LLM de résumé de texte."""

    @abstractmethod
    def summarize(self, transcript: str, language: Optional[str] = None) -> str:
        """Retourne un résumé concis du transcript.

        Args:
            transcript: Texte d'entrée à résumer.
            language: Langue attendue pour le résumé (ex: "fr", "en").
        """
        raise NotImplementedError
