from __future__ import annotations

import uuid
from typing import Dict, List

from app.domain.entities.consent_record import ConsentMethod, ConsentRecord


class InMemoryConsentStore:
    def __init__(self) -> None:
        self._by_session: Dict[str, List[ConsentRecord]] = {}

    def add(self, record: ConsentRecord) -> ConsentRecord:
        self._by_session.setdefault(record.session_id, []).append(record)
        return record

    def list_by_session(self, session_id: str) -> List[ConsentRecord]:
        return list(self._by_session.get(session_id, []))


class ConsentService:
    """Use cases: RequestConsent et StoreConsentRecord (in-memory)."""

    def __init__(self, store: InMemoryConsentStore) -> None:
        self._store = store

    def request_consent(
        self,
        session_id: str,
        participant_id: str,
        method: ConsentMethod,
        granted: bool,
        timestamp_ms: int,
    ) -> ConsentRecord:
        record = ConsentRecord(
            id=str(uuid.uuid4()),
            session_id=session_id,
            participant_id=participant_id,
            granted=granted,
            method=method,
            timestamp_ms=timestamp_ms,
        )
        return self._store.add(record)

    def list_session_consents(self, session_id: str) -> List[ConsentRecord]:
        return self._store.list_by_session(session_id)
