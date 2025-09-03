from __future__ import annotations

import os
from typing import Dict, List, Tuple

from qdrant_client import QdrantClient
from qdrant_client.conversions.common_types import ScoredPoint
from qdrant_client.http import models as qmodels


class QdrantVectorIndex:
    """Qdrant-backed vector index with a minimal API.

    Compatible with the in-memory index.

    Methods implemented:
    - add(item_id, vector, metadata)
    - search_by_vector(query_vector, top_k)
    - count()

    Collection is created on-demand.
    The vector size is inferred from the first insert.
    Distance is cosine by default.
    """

    def __init__(
        self,
        collection: str = "memories",
        url: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self._collection = collection
        self._url = url or os.getenv("NC_VECTORDB_URL", "http://localhost:6333")
        self._api_key = api_key or os.getenv("NC_QDRANT_API_KEY")
        self._client = QdrantClient(url=self._url, api_key=self._api_key)

    # ------------------------------
    # Internal helpers
    # ------------------------------
    def _ensure_collection(self, dimension: int) -> None:
        try:
            info = self._client.get_collection(self._collection)
            params = info.config.params
            if params and getattr(params, "vectors", None):
                # If exists, assume compatible
                return
        except Exception:
            pass

        self._client.recreate_collection(
            collection_name=self._collection,
            vectors_config=qmodels.VectorParams(
                size=dimension, distance=qmodels.Distance.COSINE
            ),
        )

    # ------------------------------
    # Public API
    # ------------------------------
    def add(self, item_id: str, vector: List[float], metadata: Dict[str, str]) -> None:
        if not vector:
            raise ValueError("Vector is required")
        self._ensure_collection(len(vector))
        self._client.upsert(
            collection_name=self._collection,
            points=[
                qmodels.PointStruct(
                    id=item_id,
                    vector=vector,
                    payload=metadata or {},
                )
            ],
            wait=True,
        )

    def search_by_vector(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Tuple[str, float, Dict[str, str]]]:
        if not query_vector:
            return []
        self._ensure_collection(len(query_vector))
        out: List[ScoredPoint] = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=max(1, top_k),
        )
        results: List[Tuple[str, float, Dict[str, str]]] = []
        for sp in out:
            pid = str(sp.id)
            score = float(sp.score) if sp.score is not None else 0.0
            payload = dict(sp.payload or {})
            results.append((pid, score, payload))
        return results

    def count(self) -> int:
        try:
            res = self._client.count(self._collection, exact=True)
            return int(res.count or 0)
        except Exception:
            return 0
