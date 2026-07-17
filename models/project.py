from dataclasses import dataclass


@dataclass(slots=True)
class Project:
    """Movie project metadata."""

    name: str
    title: str
    genre: str
    theme: str