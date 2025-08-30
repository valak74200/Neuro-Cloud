from dataclasses import dataclass


@dataclass(frozen=True)
class Tag:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("tag value required")


@dataclass(frozen=True)
class ImportanceScore:
    score: float  # 0.0 to 1.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("score must be between 0.0 and 1.0")
