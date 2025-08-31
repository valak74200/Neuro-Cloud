from __future__ import annotations

import uuid
from typing import List, Optional

from app.domain.entities.recall_card import RecallCard
from app.domain.entities.tag import ImportanceScore, Tag
from app.domain.entities.transcript_segment import TranscriptSegment
from app.domain.providers.summarization_provider import SummarizationProvider


class SummarizeSessionService:
    """Use case: produire un résumé d'une session sous forme de `RecallCard`."""

    def __init__(self, provider: SummarizationProvider) -> None:
        self._provider = provider

    def summarize(
        self,
        user_id: str,
        session_id: str,
        segments: List[TranscriptSegment],
        language: Optional[str] = None,
    ) -> RecallCard:
        transcript_lines: List[str] = []
        for seg in segments:
            speaker = seg.speaker_label or "Speaker"
            transcript_lines.append(f"[{speaker}] {seg.text}")
        transcript = "\n".join(transcript_lines)

        summary = self._provider.summarize(transcript, language=language)

        # Construction d'une RecallCard minimale
        title = (summary.split(". ")[0] or "Résumé de session").strip()
        tags: List[Tag] = []
        importance = ImportanceScore(0.5)
        recall = RecallCard(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title[:80],
            summary=summary,
            tags=tags,
            importance=importance,
        )
        return recall
