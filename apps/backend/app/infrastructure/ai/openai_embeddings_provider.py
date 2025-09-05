import hashlib
import os
from typing import Dict, List

import httpx
from app.domain.providers.embeddings_provider import EmbeddingsProvider


class CachedEmbeddingsProvider(EmbeddingsProvider):
    """Embeddings provider with in-memory caching to avoid duplicate API calls."""

    def __init__(self, provider: EmbeddingsProvider) -> None:
        self._provider = provider
        self._cache: Dict[str, List[float]] = {}

    def _get_cache_key(self, text: str) -> str:
        """Generate a cache key from text content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed texts with caching to avoid duplicate API calls."""
        results = []
        uncached_texts = []
        uncached_indices = []

        # Check cache for each text
        for i, text in enumerate(texts):
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                results.append(self._cache[cache_key])
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)
                results.append([])  # Placeholder

        # Call provider for uncached texts
        if uncached_texts:
            try:
                embeddings = self._provider.embed_texts(uncached_texts)

                # Store in cache and update results
                for i, embedding in enumerate(embeddings):
                    original_index = uncached_indices[i]
                    cache_key = self._get_cache_key(uncached_texts[i])
                    self._cache[cache_key] = embedding
                    results[original_index] = embedding

            except Exception as e:
                # If provider fails, return empty embeddings for uncached texts
                for i in uncached_indices:
                    results[i] = []
                raise e

        return results


class OpenAIEmbeddingsProvider(EmbeddingsProvider):
    """OpenAI embeddings provider with robust error handling."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key or os.getenv("NC_OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("NC_OPENAI_API_KEY is required")

        self._model = model or os.getenv(
            "NC_OPENAI_EMBED_MODEL", "text-embedding-3-small"
        )
        self._base_url = base_url or os.getenv(
            "NC_OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self._timeout = float(os.getenv("NC_EMBEDDINGS_TIMEOUT", "60.0"))

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts using OpenAI API."""
        if not texts:
            return []

        # Validate input
        if any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("All texts must be non-empty strings")

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {"model": self._model, "input": texts}

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/embeddings", headers=headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()

                embeddings = []
                for item in data.get("data", []):
                    embedding = item.get("embedding", [])
                    if not embedding:
                        raise ValueError("Empty embedding received from OpenAI")
                    embeddings.append(embedding)

                if len(embeddings) != len(texts):
                    raise ValueError(
                        f"Expected {len(texts)} embeddings, got {len(embeddings)}"
                    )

                return embeddings

        except httpx.TimeoutException:
            raise RuntimeError("Timeout while calling OpenAI embeddings API")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid OpenAI API key")
            elif e.response.status_code == 429:
                raise RuntimeError("OpenAI API rate limit exceeded")
            else:
                raise RuntimeError(f"OpenAI API error: {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}")


# Factory function to create cached OpenAI provider
def create_cached_openai_embeddings_provider() -> CachedEmbeddingsProvider:
    """Create a cached OpenAI embeddings provider."""
    openai_provider = OpenAIEmbeddingsProvider()
    return CachedEmbeddingsProvider(openai_provider)
