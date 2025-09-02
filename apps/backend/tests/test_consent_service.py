from app.domain.entities.consent_record import ConsentMethod
from app.services.consent_service import ConsentService, InMemoryConsentStore


def test_request_and_list_consents() -> None:
    store = InMemoryConsentStore()
    svc = ConsentService(store)

    rec = svc.request_consent(
        session_id="sess1",
        participant_id="p1",
        method=(
            ConsentMethod.__args__[0]
            if hasattr(ConsentMethod, "__args__")
            else "in_app"
        ),
        granted=True,
        timestamp_ms=1234,
    )
    assert rec.session_id == "sess1" and rec.participant_id == "p1"

    allc = svc.list_session_consents("sess1")
    assert len(allc) == 1 and allc[0].id == rec.id
