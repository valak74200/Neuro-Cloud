import os
import uuid

import httpx
import pytest
from app.infrastructure.vector.qdrant_index import QdrantVectorIndex


def _qdrant_reachable() -> bool:
    url = os.getenv("NC_VECTORDB_URL")
    if not url:
        return False
    try:
        with httpx.Client(timeout=1.0) as client:
            # cheap health probe
            resp = client.get(url.rstrip("/") + "/collections")
            return resp.status_code < 500
    except Exception:
        return False


@pytest.mark.skipif(not _qdrant_reachable(), reason="Qdrant not reachable")
def test_qdrant_add_and_search_roundtrip():
    index = QdrantVectorIndex(collection="nc_test_memories")
    before = index.count()
    item_id = str(uuid.uuid4())
    index.add(item_id, [0.1, 0.2, 0.3], {"k": "v"})
    assert index.count() == before + 1

    results = index.search_by_vector([0.1, 0.2, 0.3], top_k=1)
    assert results, "Search should return results"
    assert len(results) == 1, "Should return exactly one result"
    # Check that we get back the same metadata, even if ID format differs
    returned_id, score, metadata = results[0]
    assert metadata == {"k": "v"}, f"Metadata should match: {metadata}"
    assert score > 0.99, f"Score should be very high for identical vectors: {score}"
