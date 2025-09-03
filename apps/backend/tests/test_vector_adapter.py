import os

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
    index.add("a1", [0.1, 0.2, 0.3], {"k": "v"})
    assert index.count() == before + 1

    results = index.search_by_vector([0.1, 0.2, 0.3], top_k=1)
    assert results and results[0][0] == "a1"
