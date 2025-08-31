import os
from typing import List

import httpx
from app.domain.entities.action_item import ActionItem
from app.domain.providers.action_items_provider import ActionItemsProvider


class OpenAIActionItemsProvider(ActionItemsProvider):
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.getenv("NC_OPENAI_API_KEY")
        if not self._api_key:
            raise RuntimeError("NC_OPENAI_API_KEY is required")
        self._model = model or os.getenv("NC_OPENAI_LLM_MODEL", "gpt-4o-mini")
        self._base_url = os.getenv("NC_OPENAI_BASE_URL", "https://api.openai.com/v1")

    def extract(self, transcript: str) -> List[ActionItem]:
        system = (
            "Tu extrais les action items concrets d'une réunion. "
            "Réponds en JSON: [{description, assignee?, due_date?}]."
        )
        user = (
            "Donne la liste des actions à faire (si aucune, liste vide).\n\n"
            f"Transcript:\n{transcript}"
        )
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        url = f"{self._base_url}/chat/completions"
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "{}")
                .strip()
            )
        import json

        try:
            obj = json.loads(content)
        except Exception:
            obj = {"items": []}
        items = []
        for it in obj.get("items", []):
            items.append(
                ActionItem(
                    id=os.urandom(8).hex(),
                    description=str(it.get("description", "")).strip(),
                    assignee=it.get("assignee"),
                    due_date=it.get("due_date"),
                )
            )
        return items
