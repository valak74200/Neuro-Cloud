import os

import pytest
from app.domain.entities.transcript_segment import TranscriptSegment
from app.infrastructure.ai.openai_action_items_provider import OpenAIActionItemsProvider
from app.services.generate_action_items_service import GenerateActionItemsService

requires_key = pytest.mark.skipif(
    not os.getenv("NC_OPENAI_API_KEY"),
    reason="NC_OPENAI_API_KEY not set",
)


@requires_key
def test_generate_action_items_returns_list() -> None:
    provider = OpenAIActionItemsProvider()
    service = GenerateActionItemsService(provider)

    segs = [
        TranscriptSegment(
            id="1",
            session_id="sess",
            start_ms=0,
            end_ms=1500,
            text="Décider qui prépare la démo, livrer un brouillon avant vendredi.",
            speaker_label="Alice",
        ),
        TranscriptSegment(
            id="2",
            session_id="sess",
            start_ms=1600,
            end_ms=3200,
            text=("Bob prendra la documentation, Clara s'occupe des " "slides."),
            speaker_label="Bob",
        ),
    ]

    items = service.generate(segs)
    assert isinstance(items, list)
    # La liste peut être vide si le LLM ne détecte aucune action.
    # On vérifie ici uniquement le type retourné.
