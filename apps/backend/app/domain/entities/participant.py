from dataclasses import dataclass


@dataclass(frozen=True)
class Participant:
    id: str
    display_name: str

    def __post_init__(self) -> None:
        if not self.id or not self.display_name:
            raise ValueError("id and display_name are required")
