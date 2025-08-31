import os
from typing import List

import httpx
from app.domain.providers.embeddings_provider import EmbeddingsProvider


class OpenAIEmbeddingsProvider(EmbeddingsProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.getenv("NC_OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("NC_OPENAI_API_KEY is required")
        self._model = model or os.getenv(
            "NC_OPENAI_EMBED_MODEL", "text-embedding-3-small"
        )
        self._base_url = os.getenv("NC_OPENAI_BASE_URL", "https://api.openai.com/v1")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self._model, "input": texts}
        url = f"{self._base_url}/embeddings"
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return [item.get("embedding", []) for item in data.get("data", [])]
