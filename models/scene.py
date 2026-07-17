from dataclasses import dataclass, field


@dataclass(slots=True)
class Scene:
    """Production scene."""

    number: int

    title: str

    location: str

    time: str

    summary: str

    characters: list[str] = field(default_factory=list)

    mood: str = ""

    camera: str = ""

    lighting: str = ""