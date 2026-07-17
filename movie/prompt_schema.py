"""Structured image-prompt records for storyboard shots."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class PromptRecord:
    id: str
    scene_number: int
    shot_number: int
    style_id: str
    model_template: str = "generic"
    prompt: str = ""
    negative_prompt: str = ""
    character_names: list[str] = field(default_factory=list)
    location_name: str = ""
    prop_names: list[str] = field(default_factory=list)
    director_note: str = ""
    quality_score: int = 0
    warnings: list[str] = field(default_factory=list)
    version: int = 1
    status: str = "ready"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PromptRecord":
        return cls(
            id=str(data.get("id", "")).strip(),
            scene_number=max(1, int(data.get("scene_number", 1))),
            shot_number=max(1, int(data.get("shot_number", 1))),
            style_id=str(data.get("style_id", "cinematic_naturalism")).strip(),
            model_template=str(data.get("model_template", "generic")).strip(),
            prompt=str(data.get("prompt", "")).strip(),
            negative_prompt=str(data.get("negative_prompt", "")).strip(),
            character_names=[str(x).strip() for x in data.get("character_names", []) if str(x).strip()],
            location_name=str(data.get("location_name", "")).strip(),
            prop_names=[str(x).strip() for x in data.get("prop_names", []) if str(x).strip()],
            director_note=str(data.get("director_note", "")).strip(),
            quality_score=max(0, min(100, int(data.get("quality_score", 0)))),
            warnings=[str(x).strip() for x in data.get("warnings", []) if str(x).strip()],
            version=max(1, int(data.get("version", 1))),
            status=str(data.get("status", "ready")).strip() or "ready",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
