"""Location Bible data model."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        return "; ".join(f"{k}: {_text(v)}" for k, v in value.items() if _text(v))
    if isinstance(value, list):
        return ", ".join(_text(v) for v in value if _text(v))
    return str(value or "").strip()


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (_text(v) for v in value) if item]
    text = _text(value)
    return [item.strip() for item in text.split(",") if item.strip()] if text else []

@dataclass
class LocationBible:
    name: str
    type: str = ""
    architecture: str = ""
    layout: str = ""
    lighting: str = ""
    color_palette: list[str] = field(default_factory=list)
    atmosphere: str = ""
    recurring_objects: list[str] = field(default_factory=list)
    exterior: str = ""
    interior: str = ""
    consistency_prompt: str = ""
    negative_prompt: str = ""
    status: str = "draft"
    id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any], fallback_name: str = "") -> "LocationBible":
        name = _text(data.get("name") or fallback_name)
        if not name:
            raise ValueError("Location name is required.")
        return cls(
            name=name,
            type=_text(data.get("type")),
            architecture=_text(data.get("architecture")),
            layout=_text(data.get("layout")),
            lighting=_text(data.get("lighting")),
            color_palette=_list(data.get("color_palette")),
            atmosphere=_text(data.get("atmosphere")),
            recurring_objects=_list(data.get("recurring_objects")),
            exterior=_text(data.get("exterior")),
            interior=_text(data.get("interior")),
            consistency_prompt=_text(data.get("consistency_prompt")),
            negative_prompt=_text(data.get("negative_prompt")),
            status=_text(data.get("status")) or "draft",
            id=_text(data.get("id")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
