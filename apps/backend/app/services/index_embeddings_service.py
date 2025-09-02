from __future__ import annotations

import math
from typing import Dict, List, Tuple

from app.domain.entities.transcript_segment import TranscriptSegment
from app.domain.providers.embeddings_provider import EmbeddingsProvider


class InMemoryVectorIndex:
    """Index vectoriel en mémoire (simple) pour tests."""

    def __init__(self) -> None:
        self._store: List[Tuple[str, List[float], Dict[str, str]]] = []

    def add(self, item_id: str, vector: List[float], metadata: Dict[str, str]) -> None:
        self._store.append((item_id, vector, metadata))

    def count(self) -> int:
        return len(self._store)

    def items(self) -> List[Tuple[str, List[float], Dict[str, str]]]:
        return list(self._store)

    def search_by_vector(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Tuple[str, float, Dict[str, str]]]:
        def cosine(a: List[float], b: List[float]) -> float:
            if not a or not b or len(a) != len(b):
                return 0.0
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            if na == 0.0 or nb == 0.0:
                return 0.0
            return dot / (na * nb)

        scored: List[Tuple[str, float, Dict[str, str]]] = []
        for item_id, vec, meta in self._store:
            scored.append((item_id, cosine(query_vector, vec), meta))
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[: max(1, top_k)]


class IndexEmbeddingsService:
    """Use case: générer et indexer les embeddings des segments d'une session."""

    def __init__(
        self, provider: EmbeddingsProvider, index: InMemoryVectorIndex
    ) -> None:
        self._provider = provider
        self._index = index

    def index_segments(self, session_id: str, segments: List[TranscriptSegment]) -> int:
        texts = [s.text for s in segments]
        vectors = self._provider.embed_texts(texts)
        for seg, vec in zip(segments, vectors):
            self._index.add(
                item_id=seg.id,
                vector=vec,
                metadata={"session_id": session_id, "speaker": seg.speaker_label or ""},
            )
        return self._index.count()
