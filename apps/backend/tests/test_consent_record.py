import pytest
from app.domain.entities.consent_record import ConsentRecord


def test_consent_record_valid():
    c = ConsentRecord(
        id="c1",
        session_id="s1",
        participant_id="p1",
        granted=True,
        method="in_app",
        timestamp_ms=10,
    )
    assert c.granted is True


def test_consent_record_validations():
    with pytest.raises(ValueError):
        ConsentRecord(
            id="x",
            session_id="",
            participant_id="p",
            granted=True,
            method="verbal",
            timestamp_ms=0,
        )
    with pytest.raises(ValueError):
        ConsentRecord(
            id="x",
            session_id="s",
            participant_id="",
            granted=True,
            method="verbal",
            timestamp_ms=0,
        )
    with pytest.raises(ValueError):
        ConsentRecord(
            id="x",
            session_id="s",
            participant_id="p",
            granted=True,
            method="verbal",
            timestamp_ms=-1,
        )
