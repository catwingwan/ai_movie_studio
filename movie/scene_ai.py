"""Local-AI extraction of production scenes from a screenplay."""

from __future__ import annotations

from typing import Any

from ai.provider import ask_json
from config.prompts import SCENE_PROMPT
from movie.scene_schema import Scene


def build_scene_prompt(screenplay: str) -> str:
    """Insert screenplay text without interpreting JSON braces in the prompt.

    ``str.format`` cannot be used here because SCENE_PROMPT contains a JSON
    example. Its braces would be treated as format fields and can raise errors
    such as ``KeyError: '\n  "number"'``.
    """
    prompt = SCENE_PROMPT
    prompt = prompt.replace("{screenplay}", screenplay)
    prompt = prompt.replace("{story}", screenplay)
    return prompt


def extract_scenes(screenplay: str) -> list[Scene]:
    data: Any = ask_json(build_scene_prompt(screenplay))
    if isinstance(data, dict):
        data = data.get("scenes", data.get("items", []))
    if not isinstance(data, list) or not data:
        raise ValueError("The local AI did not return a valid scene list.")

    scenes: list[Scene] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Scene {index} is not a JSON object.")
        scenes.append(Scene.from_dict(item, index))

    # Normalize numbering so filenames and downstream storyboard ordering stay stable.
    normalized: list[Scene] = []
    for number, scene in enumerate(scenes, start=1):
        scene.scene_number = number
        scene.id = f"scene_{number:03d}"
        normalized.append(scene)
    return normalized
