import pytest
from app.domain.entities.retention_policy import RetentionPolicy


def test_retention_policy_valid():
    p = RetentionPolicy(amount=30, unit="days")
    assert p.amount == 30
    assert p.unit == "days"


def test_retention_policy_amount_positive():
    with pytest.raises(ValueError):
        RetentionPolicy(amount=0, unit="days")
