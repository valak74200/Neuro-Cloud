from __future__ import annotations

from typing import List

from app.domain.entities.action_item import ActionItem
from app.domain.entities.transcript_segment import TranscriptSegment
from app.domain.providers.action_items_provider import ActionItemsProvider


class GenerateActionItemsService:
    """Use case: générer des items d'action à partir d'une session transcrite."""

    def __init__(self, provider: ActionItemsProvider) -> None:
        self._provider = provider

    def generate(self, segments: List[TranscriptSegment]) -> List[ActionItem]:
        # Concatène le transcript multi-segments pour extraction
        lines: List[str] = []
        for seg in segments:
            who = seg.speaker_label or "Speaker"
            lines.append(f"[{who}] {seg.text}")
        transcript = "\n".join(lines)
        return self._provider.extract(transcript)
