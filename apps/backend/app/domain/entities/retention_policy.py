from dataclasses import dataclass
from typing import Literal

PolicyUnit = Literal["days", "weeks", "months"]


@dataclass(frozen=True)
class RetentionPolicy:
    amount: int
    unit: PolicyUnit

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("amount must be positive")
