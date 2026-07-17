"""AI generation helpers for location and prop production bibles."""
from __future__ import annotations
import json
import re
from typing import Any
from ai.provider import ask
from movie.character_bible_ai import parse_response
from movie.location_bible_schema import LocationBible
from movie.prop_schema import PropAsset

LOCATION_PROMPT = """You are creating a reusable location bible for a free, local, open-source AI movie pipeline.
Return EXACTLY ONE valid JSON object and no Markdown.
Use flat strings and arrays of strings only. Do not use nested objects.
Required keys: name, type, architecture, layout, lighting, color_palette, atmosphere,
recurring_objects, exterior, interior, consistency_prompt, negative_prompt, status.
The consistency_prompt must describe a repeatable visual identity for image generation.
The negative_prompt must prevent layout drift, inconsistent architecture, text, logos, watermarks, people duplication, and malformed geometry.
status must be "draft".
LOCATION NAME: __NAME__
SCENES USING THIS LOCATION:
__SCENES__
"""

PROP_PROMPT = """You are identifying visually important recurring props for a free, local, open-source AI movie pipeline.
Return ONLY a valid JSON array. Each item must be one flat JSON object.
Include only concrete visible objects important for story continuity or repeated shots. Ignore generic furniture unless story-relevant.
Required keys per item: name, category, description, materials, colors, condition, story_function,
scenes, consistency_prompt, negative_prompt, status.
materials and colors are arrays of strings. scenes is an array of scene numbers. status is "draft".
Do not include brands, logos, paid services, or copyrighted characters.
SCENE JSON:
__SCENE__
"""


def _repair_array(text: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(text).strip(), flags=re.I)
    start = min([p for p in (cleaned.find("["), cleaned.find("{")) if p >= 0], default=-1)
    if start < 0:
        raise ValueError(f"Invalid JSON returned by AI: {cleaned}")
    candidate = cleaned[start:]
    decoder = json.JSONDecoder()
    values: list[Any] = []
    index = 0
    while index < len(candidate):
        while index < len(candidate) and candidate[index] in " \t\r\n,":
            index += 1
        if index >= len(candidate):
            break
        try:
            value, end = decoder.raw_decode(candidate, index)
            values.append(value)
            index = end
        except json.JSONDecodeError:
            # Reuse tolerant object parser when the model returned one object.
            try:
                values.append(parse_response(candidate[index:]))
                break
            except ValueError as error:
                raise ValueError(f"Invalid JSON returned by AI: {cleaned}") from error
    if len(values) == 1 and isinstance(values[0], list):
        return values[0]
    if values and all(isinstance(v, dict) for v in values):
        return values
    raise ValueError(f"Invalid JSON returned by AI: {cleaned}")


def generate_location_bible(name: str, scenes: list[dict[str, Any]]) -> LocationBible:
    prompt = LOCATION_PROMPT.replace("__NAME__", name).replace(
        "__SCENES__", json.dumps(scenes, indent=2, ensure_ascii=False)
    )
    return LocationBible.from_dict(parse_response(ask(prompt)), name)


def generate_props_for_scene(scene: dict[str, Any]) -> list[PropAsset]:
    prompt = PROP_PROMPT.replace("__SCENE__", json.dumps(scene, indent=2, ensure_ascii=False))
    raw = _repair_array(ask(prompt))
    if not isinstance(raw, list):
        raise ValueError("Prop AI did not return a JSON array.")
    result: list[PropAsset] = []
    scene_number = int(scene.get("scene_number", scene.get("number", 0)) or 0)
    for item in raw:
        if not isinstance(item, dict):
            continue
        item.setdefault("scenes", [scene_number] if scene_number else [])
        try:
            result.append(PropAsset.from_dict(item))
        except ValueError:
            continue
    return result
