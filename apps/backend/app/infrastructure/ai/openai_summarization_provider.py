import hashlib
import logging
import os
from typing import Dict, List, Optional

import httpx
from app.domain.providers.summarization_provider import SummarizationProvider

logger = logging.getLogger(__name__)


class CachedSummarizationProvider(SummarizationProvider):
    """Summarization provider with in-memory caching."""

    def __init__(self, provider: SummarizationProvider) -> None:
        self._provider = provider
        self._cache: Dict[str, str] = {}

    def _get_cache_key(self, transcript: str, language: Optional[str] = None) -> str:
        """Generate a cache key from transcript and language."""
        content = f"{transcript}|{language or 'auto'}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def summarize(self, transcript: str, language: Optional[str] = None) -> str:
        """Summarize with caching to avoid duplicate API calls."""
        if not transcript or not transcript.strip():
            return ""

        cache_key = self._get_cache_key(transcript, language)
        if cache_key in self._cache:
            logger.debug("Using cached summary")
            return self._cache[cache_key]

        summary = self._provider.summarize(transcript, language)
        if summary:  # Only cache non-empty summaries
            self._cache[cache_key] = summary

        return summary


class OpenAISummarizationProvider(SummarizationProvider):
    """OpenAI-powered summarization provider with robust error handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        request_timeout_seconds: float = 60.0,
    ) -> None:
        self._api_key = api_key or os.getenv("NC_OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("NC_OPENAI_API_KEY is required")

        self._model = model or os.getenv("NC_OPENAI_LLM_MODEL", "gpt-4o-mini")
        self._base_url = base_url or os.getenv(
            "NC_OPENAI_BASE_URL", "https://api.openai.com/v1"
        )
        self._timeout = request_timeout_seconds

        # Fallback models in order of preference
        self._fallback_models = [
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-4",
        ]

    def summarize(self, transcript: str, language: Optional[str] = None) -> str:
        """Generate a summary using OpenAI with fallback support."""
        if not transcript or not transcript.strip():
            return ""

        # Validate input length (OpenAI has token limits)
        if len(transcript) > 100000:  # ~25k tokens safety margin
            logger.warning(f"Transcript too long ({len(transcript)} chars), truncating")
            transcript = transcript[:50000] + "...[truncated]"

        lang = language or os.getenv("NC_SUMMARY_LANGUAGE", "fr")

        # Try primary model first, then fallbacks
        for model in [self._model] + self._fallback_models:
            if model == self._model or model not in [self._model]:
                try:
                    return self._summarize_with_model(transcript, lang, model)
                except Exception as e:
                    logger.warning(f"Failed with model {model}: {e}")
                    if model == self._fallback_models[-1]:
                        # Last fallback failed, raise the error
                        raise e
                    continue

        # This should never be reached, but just in case
        raise RuntimeError("All summarization models failed")

    def _summarize_with_model(self, transcript: str, language: str, model: str) -> str:
        """Summarize using a specific model."""
        system_prompt = (
            "Tu es un assistant expert qui produit des résumés structurés, "
            "concis et factuels. Mets en avant les décisions, actions et points clés."
        )

        user_prompt = (
            f"Résumé en {language} du contenu suivant, en 4-6 phrases maximum. "
            "Concentre-toi sur les décisions prises, les actions à mener et "
            f"les points importants.\n\nContenu à résumer:\n{transcript}"
        )

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,  # Low temperature for consistent summaries
            "max_tokens": 500,  # Limit output length
        }

        try:
            with httpx.Client(timeout=self._timeout) as client:
                resp = client.post(
                    f"{self._base_url}/chat/completions", headers=headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()

                choices = data.get("choices", [])
                if not choices:
                    raise ValueError("No choices returned from OpenAI")

                message = choices[0].get("message", {})
                content = message.get("content", "").strip()

                if not content:
                    raise ValueError("Empty summary returned from OpenAI")

                logger.info(f"Successfully summarized with model {model}")
                return content

        except httpx.TimeoutException:
            raise RuntimeError(f"Timeout while calling OpenAI {model}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise RuntimeError("Invalid OpenAI API key")
            elif e.response.status_code == 429:
                raise RuntimeError("OpenAI API rate limit exceeded")
            elif e.response.status_code == 400:
                raise RuntimeError(f"Bad request to OpenAI {model}: {e.response.text}")
            else:
                raise RuntimeError(f"OpenAI API error {e.response.status_code}")
        except Exception as e:
            raise RuntimeError(f"Failed to generate summary with {model}: {str(e)}")


class FallbackSummarizationProvider(SummarizationProvider):
    """Summarization provider with multiple fallback strategies."""

    def __init__(self, providers: List[SummarizationProvider]) -> None:
        if not providers:
            raise ValueError("At least one provider is required")
        self._providers = providers

    def summarize(self, transcript: str, language: Optional[str] = None) -> str:
        """Try providers in order until one succeeds."""
        last_error = None

        for i, provider in enumerate(self._providers):
            try:
                logger.info(
                    f"Trying summarization provider {i + 1}/{len(self._providers)}"
                )
                return provider.summarize(transcript, language)
            except Exception as e:
                logger.warning(f"Provider {i + 1} failed: {e}")
                last_error = e
                continue

        # All providers failed
        raise RuntimeError(
            f"All summarization providers failed. Last error: {last_error}"
        )


# Factory functions
def create_cached_openai_summarizer() -> CachedSummarizationProvider:
    """Create a cached OpenAI summarization provider."""
    openai_provider = OpenAISummarizationProvider()
    return CachedSummarizationProvider(openai_provider)


def create_fallback_summarizer() -> FallbackSummarizationProvider:
    """Create a summarizer with fallback to multiple providers."""
    # For now, just OpenAI with fallbacks, but could be extended
    openai_provider = OpenAISummarizationProvider()
    cached_provider = CachedSummarizationProvider(openai_provider)

    # Could add more providers here in the future
    return FallbackSummarizationProvider([cached_provider])
