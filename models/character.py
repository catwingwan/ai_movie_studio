from dataclasses import dataclass


@dataclass(slots=True)
class Character:
    """Movie character."""

    name: str
    role: str
    description: str