"""Prop Library data model."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
from movie.location_bible_schema import _list, _text

@dataclass
class PropAsset:
    name: str
    category: str = ""
    description: str = ""
    materials: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)
    condition: str = ""
    story_function: str = ""
    scenes: list[int] = field(default_factory=list)
    consistency_prompt: str = ""
    negative_prompt: str = ""
    status: str = "draft"
    id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], fallback_name: str = "") -> "PropAsset":
        name = _text(data.get("name") or fallback_name)
        if not name:
            raise ValueError("Prop name is required.")
        raw_scenes = data.get("scenes", [])
        if not isinstance(raw_scenes, list):
            raw_scenes = [raw_scenes]
        scenes: list[int] = []
        for value in raw_scenes:
            try:
                number = int(value)
                if number > 0 and number not in scenes:
                    scenes.append(number)
            except (TypeError, ValueError):
                continue
        return cls(
            name=name,
            category=_text(data.get("category")),
            description=_text(data.get("description")),
            materials=_list(data.get("materials")),
            colors=_list(data.get("colors")),
            condition=_text(data.get("condition")),
            story_function=_text(data.get("story_function")),
            scenes=scenes,
            consistency_prompt=_text(data.get("consistency_prompt")),
            negative_prompt=_text(data.get("negative_prompt")),
            status=_text(data.get("status")) or "draft",
            id=_text(data.get("id")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
