from __future__ import annotations

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
