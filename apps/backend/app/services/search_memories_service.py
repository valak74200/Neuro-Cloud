from __future__ import annotations

from typing import List, Tuple

from app.domain.providers.embeddings_provider import EmbeddingsProvider
from app.services.index_embeddings_service import InMemoryVectorIndex


class SearchMemoriesService:
    """Recherche sémantique simple sur l'index mémoire en mémoire."""

    def __init__(
        self, provider: EmbeddingsProvider, index: InMemoryVectorIndex
    ) -> None:
        self._provider = provider
        self._index = index

    def search(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        vectors = self._provider.embed_texts([query])
        if not vectors:
            return []
        qv = vectors[0]
        results = self._index.search_by_vector(qv, top_k=top_k)
        return [(item_id, score) for item_id, score, _ in results]
