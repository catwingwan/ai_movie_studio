"""Local Director AI analysis for scenes and storyboards."""

from __future__ import annotations

import json
import re
from typing import Any

from ai.provider import ask
from movie.director_schema import DirectorReview
from movie.scene_schema import Scene
from movie.storyboard_schema import StoryboardShot


DIRECTOR_PROMPT = """You are a practical film director reviewing one scene before image and video generation.

Review the scene and its storyboard shots. Return EXACTLY ONE valid JSON object. Do not use Markdown. Do not return multiple JSON objects.

The single JSON object must contain all of these keys:
- overall_score
- emotion_score
- pacing_score
- dialogue_score
- visual_interest_score
- continuity_score
- strengths
- concerns
- recommendations
- shot_recommendations
- sound_recommendations
- director_note

Use integer scores from 1 to 5. Use JSON arrays of concise strings for all list fields.

Rules:
- Preserve the writer's intent and character continuity.
- Prefer practical changes that can be applied with free local open-source image/video tools.
- Do not recommend buying, renting, subscribing to, or investing in equipment or paid services.
- Do not recommend cloud-only tools.
- Avoid vague praise. Be specific and production-oriented.
- Keep each list to at most 5 items.
- Output only the single JSON object, with no prose before or after it.

SCENE JSON:
__SCENE_JSON__

STORYBOARD SHOTS JSON:
__SHOTS_JSON__
"""


def build_director_prompt(scene: Scene, shots: list[StoryboardShot]) -> str:
    scene_json = json.dumps(scene.to_dict(), indent=2, ensure_ascii=False)
    shots_json = json.dumps(
        [shot.to_dict() for shot in shots],
        indent=2,
        ensure_ascii=False,
    )
    return (
        DIRECTOR_PROMPT
        .replace("__SCENE_JSON__", scene_json)
        .replace("__SHOTS_JSON__", shots_json)
    )


def _strip_markdown_fences(text: str) -> str:
    """Remove common Markdown JSON fences without changing JSON content."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _repair_truncated_json(text: str) -> str:
    """Safely close unterminated JSON containers from a truncated response.

    This only appends missing ``]`` and ``}`` characters when strings are
    already closed and all existing brackets are correctly nested. It does
    not guess missing values, commas, quotes, or field content.
    """
    stack: list[str] = []
    in_string = False
    escaped = False

    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if not stack:
                return text
            opening = stack.pop()
            if (opening, char) not in (("{", "}"), ("[", "]")):
                return text

    # An unfinished string cannot be repaired without inventing content.
    if in_string or escaped:
        return text

    closers = {"{": "}", "[": "]"}
    return text + "".join(closers[item] for item in reversed(stack))


def _decode_json_objects(text: str) -> list[Any]:
    """Decode one or more adjacent JSON values from a model response.

    Small local models sometimes return two objects back-to-back, for example
    one object containing scores and another containing notes.  ``json.loads``
    rejects this as trailing data, but each object is otherwise valid.
    """
    cleaned = _strip_markdown_fences(text)
    decoder = json.JSONDecoder()
    values: list[Any] = []
    index = 0

    while index < len(cleaned):
        while index < len(cleaned) and (
            cleaned[index].isspace() or cleaned[index] in ",;"
        ):
            index += 1
        if index >= len(cleaned):
            break

        try:
            value, end = decoder.raw_decode(cleaned, index)
        except json.JSONDecodeError:
            # The local model may be cut off after producing all fields but
            # before writing the final closing brace. Repair only missing
            # closing containers, never missing values or quotes.
            repaired = _repair_truncated_json(cleaned[index:])
            if repaired != cleaned[index:]:
                try:
                    value, relative_end = decoder.raw_decode(repaired, 0)
                except json.JSONDecodeError:
                    pass
                else:
                    values.append(value)
                    index += relative_end
                    continue

            # Skip harmless explanatory text until the next JSON container.
            starts = [
                pos for pos in (
                    cleaned.find("{", index + 1),
                    cleaned.find("[", index + 1),
                )
                if pos != -1
            ]
            if not starts:
                raise ValueError(f"Invalid JSON returned by AI: {cleaned}")
            index = min(starts)
            continue

        values.append(value)
        index = end

    if not values:
        raise ValueError(f"Invalid JSON returned by AI: {cleaned}")
    return values


def parse_director_response(response: Any) -> dict[str, Any]:
    """Normalize common local-model JSON response shapes into one review dict."""
    if isinstance(response, dict):
        values: list[Any] = [response]
    elif isinstance(response, list):
        values = response
    elif isinstance(response, str):
        values = _decode_json_objects(response)
    else:
        raise ValueError(f"Invalid Director AI response type: {type(response).__name__}")

    merged: dict[str, Any] = {}
    for value in values:
        if isinstance(value, dict) and isinstance(value.get("review"), dict):
            value = value["review"]
        if not isinstance(value, dict):
            continue
        merged.update(value)

    if not merged:
        raise ValueError("Local AI returned no usable Director review object.")
    return merged


def generate_director_review(
    scene: Scene,
    shots: list[StoryboardShot],
) -> DirectorReview:
    raw_response = ask(build_director_prompt(scene, shots))
    data = parse_director_response(raw_response)
    return DirectorReview.from_dict(data, scene.scene_number, scene.heading)
