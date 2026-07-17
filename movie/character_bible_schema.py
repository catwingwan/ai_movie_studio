"""Validated character-bible model used by image prompt generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _text(value: Any) -> str:
    """Normalize strings as well as nested AI objects into readable text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        preferred = []
        for key in ("description", "type", "shape", "style", "color", "level", "texture", "size", "angles", "shading", "muscle_definition"):
            item = _text(value.get(key))
            if item and item not in preferred:
                preferred.append(item)
        tags = value.get("tags")
        if isinstance(tags, list):
            preferred.extend(_text(item) for item in tags if _text(item) not in preferred)
        if preferred:
            return ", ".join(preferred)
        return ", ".join(
            item for item in (_text(item) for item in value.values()) if item
        )
    if isinstance(value, list):
        return "; ".join(item for item in (_text(item) for item in value) if item)
    return str(value).strip()


def _height(value: Any) -> str:
    text = _text(value)
    while text.endswith('""'):
        text = text[:-1]
    return text


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (_text(item) for item in value) if item]
    if isinstance(value, dict):
        text = _text(value)
        return [text] if text else []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


@dataclass
class CharacterBible:
    id: str
    name: str
    role: str = ""
    age: str = ""
    gender_presentation: str = ""
    face: str = ""
    hair: str = ""
    eyes: str = ""
    skin_tone: str = ""
    body_type: str = ""
    height: str = ""
    distinguishing_features: list[str] = field(default_factory=list)
    personality: str = ""
    default_wardrobe: list[str] = field(default_factory=list)
    color_palette: list[str] = field(default_factory=list)
    consistency_prompt: str = ""
    negative_prompt: str = ""
    status: str = "draft"

    @classmethod
    def from_dict(cls, data: dict[str, Any], fallback: dict[str, Any]) -> "CharacterBible":
        name = _text(data.get("name") or fallback.get("name"))
        if not name:
            raise ValueError("Character Bible has no character name.")
        asset_id = _text(data.get("id")) or name
        consistency = _text(data.get("consistency_prompt") or data.get("reference_prompt"))
        if not consistency:
            details = [
                _text(data.get("age") or fallback.get("age")),
                _text(data.get("face")),
                _text(data.get("hair")),
                _text(data.get("eyes")),
                _text(data.get("skin_tone")),
                _text(data.get("body_type")),
            ]
            consistency = ", ".join(item for item in details if item)
        return cls(
            id=asset_id,
            name=name,
            role=_text(data.get("role") or fallback.get("role")),
            age=_text(data.get("age") or fallback.get("age")),
            gender_presentation=_text(data.get("gender_presentation")),
            face=_text(data.get("face")),
            hair=_text(data.get("hair")),
            eyes=_text(data.get("eyes")),
            skin_tone=_text(data.get("skin_tone")),
            body_type=_text(data.get("body_type")),
            height=_height(data.get("height")),
            distinguishing_features=_list(data.get("distinguishing_features")),
            personality=_text(data.get("personality") or fallback.get("personality")),
            default_wardrobe=_list(data.get("default_wardrobe") or data.get("wardrobe")),
            color_palette=_list(data.get("color_palette")),
            consistency_prompt=consistency,
            negative_prompt=_text(data.get("negative_prompt")),
            status=_text(data.get("status")) or "draft",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
