"""Validated scene data model used by the production pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class DialogueLine:
    character: str
    text: str

    @classmethod
    def from_value(cls, value: Any) -> "DialogueLine":
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(
                character=str(value.get("character", "")).strip(),
                text=str(value.get("text", value.get("dialogue", ""))).strip(),
            )
        return cls(character="", text=str(value).strip())


@dataclass(slots=True)
class Scene:
    id: str
    scene_number: int
    heading: str
    location: str = ""
    time: str = ""
    characters: list[str] = field(default_factory=list)
    summary: str = ""
    action: str = ""
    dialogue: list[DialogueLine] = field(default_factory=list)
    duration_seconds: int = 60
    status: str = "draft"

    @property
    def number(self) -> int:
        """Backward-compatible alias used by older UI code."""
        return self.scene_number

    @property
    def title(self) -> str:
        return self.heading

    @classmethod
    def from_dict(cls, data: dict[str, Any], default_number: int) -> "Scene":
        number_value = data.get("scene_number", data.get("number", default_number))
        try:
            number = max(1, int(number_value))
        except (TypeError, ValueError):
            number = default_number

        heading = str(
            data.get("heading", data.get("title", f"SCENE {number}"))
        ).strip()
        if not heading:
            heading = f"SCENE {number}"

        raw_characters = data.get("characters", [])
        if isinstance(raw_characters, str):
            raw_characters = [part.strip() for part in raw_characters.split(",")]
        characters = [str(item).strip() for item in raw_characters if str(item).strip()]

        raw_dialogue = data.get("dialogue", [])
        if isinstance(raw_dialogue, dict):
            raw_dialogue = [raw_dialogue]
        dialogue = [
            DialogueLine.from_value(item)
            for item in raw_dialogue
            if item is not None
        ]

        duration_value = data.get(
            "duration_seconds",
            data.get("estimated_duration_seconds", data.get("duration", 60)),
        )
        try:
            duration = max(1, int(duration_value))
        except (TypeError, ValueError):
            duration = 60

        return cls(
            id=f"scene_{number:03d}",
            scene_number=number,
            heading=heading,
            location=str(data.get("location", "")).strip(),
            time=str(data.get("time", data.get("time_of_day", ""))).strip(),
            characters=characters,
            summary=str(data.get("summary", "")).strip(),
            action=str(data.get("action", data.get("description", ""))).strip(),
            dialogue=dialogue,
            duration_seconds=duration,
            status=str(data.get("status", "draft")).strip() or "draft",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
