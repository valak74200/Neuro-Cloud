import os

import pytest
from app.domain.entities.transcript_segment import TranscriptSegment
from app.infrastructure.ai.openai_embeddings_provider import OpenAIEmbeddingsProvider
from app.services.index_embeddings_service import (
    IndexEmbeddingsService,
    InMemoryVectorIndex,
)

requires_key = pytest.mark.skipif(
    not os.getenv("NC_OPENAI_API_KEY"),
    reason="NC_OPENAI_API_KEY not set",
)


@requires_key
def test_index_embeddings_counts_items() -> None:
    provider = OpenAIEmbeddingsProvider()
    index = InMemoryVectorIndex()
    service = IndexEmbeddingsService(provider, index)

    segs = [
        TranscriptSegment(
            id="a",
            session_id="sess",
            start_ms=0,
            end_ms=1000,
            text="Bonjour, ceci est un test d'indexation.",
            speaker_label="S1",
        ),
        TranscriptSegment(
            id="b",
            session_id="sess",
            start_ms=1200,
            end_ms=2200,
            text="Deuxième segment pour vérifier le comptage.",
            speaker_label="S2",
        ),
    ]

    count = service.index_segments("sess", segs)
    assert count == 2
