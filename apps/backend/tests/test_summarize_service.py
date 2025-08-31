import os

import pytest
from app.domain.entities.transcript_segment import TranscriptSegment
from app.infrastructure.ai.openai_summarization_provider import (
    OpenAISummarizationProvider,
)
from app.services.summarize_session_service import SummarizeSessionService

requires_key = pytest.mark.skipif(
    not os.getenv("NC_OPENAI_API_KEY"),
    reason="NC_OPENAI_API_KEY not set",
)


@requires_key
def test_summarize_session_returns_recall_card() -> None:
    provider = OpenAISummarizationProvider()
    service = SummarizeSessionService(provider)

    segs = [
        TranscriptSegment(
            id="s1",
            session_id="sess",
            start_ms=0,
            end_ms=2000,
            text="Discussion sur le planning de la release la semaine prochaine.",
            speaker_label="Alice",
        ),
        TranscriptSegment(
            id="s2",
            session_id="sess",
            start_ms=2100,
            end_ms=4000,
            text="Décisions: décaler la mise en prod au mardi; action items attribués.",
            speaker_label="Bob",
        ),
    ]

    card = service.summarize(
        user_id="u1",
        session_id="sess",
        segments=segs,
        language=os.getenv("NC_SUMMARY_LANGUAGE", "fr"),
    )

    assert card.summary and len(card.summary) > 10
    assert card.title and len(card.title) > 0
    assert card.user_id == "u1"
