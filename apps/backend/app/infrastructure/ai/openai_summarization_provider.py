import os
from typing import Optional

import httpx
from app.domain.providers.summarization_provider import SummarizationProvider


class OpenAISummarizationProvider(SummarizationProvider):
    """Implémentation OpenAI (Chat Completions) du provider de résumé."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
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

    def summarize(self, transcript: str, language: Optional[str] = None) -> str:
        lang = language or os.getenv("NC_SUMMARY_LANGUAGE", "fr")

        system_prompt = (
            "Tu es un assistant qui produit des résumés structurés, concis et factuels."
        )
        user_prompt = (
            f"Résumé en {lang} du contenu suivant, en 4-6 phrases maximum, "
            "mettant en avant décisions et actions s'il y en a.\n\n"
            f"Contenu:\n{transcript}"
        )
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }

        url = f"{self._base_url}/chat/completions"
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                return ""
            message = choices[0].get("message", {})
            return message.get("content", "").strip()
