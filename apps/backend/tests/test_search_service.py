import os

import pytest
from app.domain.entities.transcript_segment import TranscriptSegment
from app.infrastructure.ai.openai_embeddings_provider import OpenAIEmbeddingsProvider
from app.services.index_embeddings_service import (
    IndexEmbeddingsService,
    InMemoryVectorIndex,
)
from app.services.search_memories_service import SearchMemoriesService

requires_key = pytest.mark.skipif(
    not os.getenv("NC_OPENAI_API_KEY"),
    reason="NC_OPENAI_API_KEY not set",
)


@requires_key
def test_search_returns_hits() -> None:
    provider = OpenAIEmbeddingsProvider()
    index = InMemoryVectorIndex()
    indexer = IndexEmbeddingsService(provider, index)

    segs = [
        TranscriptSegment(
            id="1",
            session_id="s",
            start_ms=0,
            end_ms=1000,
            text="plan de release mardi",
            speaker_label="A",
        ),
        TranscriptSegment(
            id="2",
            session_id="s",
            start_ms=1100,
            end_ms=2100,
            text="budget marketing Q4",
            speaker_label="B",
        ),
    ]
    indexer.index_segments("s", segs)

    service = SearchMemoriesService(provider, index)
    hits = service.search("release mardi", top_k=1)
    assert hits and hits[0][0] == "1"
