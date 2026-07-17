"""Local-AI generation of cinematic shots from structured scene data."""

from __future__ import annotations

import json
from typing import Any

from ai.provider import ask_json
from movie.scene_schema import Scene
from movie.storyboard_schema import StoryboardShot


STORYBOARD_PROMPT = """You are a professional film director and storyboard artist.

Break the production scene below into a concise cinematic shot list suitable for
local AI image generation and later video generation.

Return ONLY valid JSON as either a JSON array or an object with a \"shots\" array.
Do not use Markdown fences and do not add explanations.

Each shot must contain:
- shot_number
- shot_type (for example: Establishing Shot, Wide Shot, Medium Shot, Close Up, Insert)
- camera_angle
- lens
- movement
- composition
- lighting
- mood
- subject
- action
- duration_seconds (1 to 10)
- image_prompt (detailed visual prompt; do not include camera brand names)
- negative_prompt

Rules:
- Use 3 to 8 shots depending on scene complexity.
- Preserve character, location, time, action, and emotional continuity.
- Keep the total shot duration reasonably close to the scene duration.
- Avoid unnecessary shots.
- The prompts must be safe, visual, and reusable by open-source image models.

SCENE JSON:
__SCENE_JSON__
"""


def build_storyboard_prompt(scene: Scene) -> str:
    scene_json = json.dumps(scene.to_dict(), indent=2, ensure_ascii=False)
    return STORYBOARD_PROMPT.replace("__SCENE_JSON__", scene_json)


def generate_scene_shots(scene: Scene) -> list[StoryboardShot]:
    data: Any = ask_json(build_storyboard_prompt(scene))
    if isinstance(data, dict):
        data = data.get("shots", data.get("items", []))
    if not isinstance(data, list) or not data:
        raise ValueError(f"Local AI returned no valid shots for scene {scene.scene_number}.")

    shots: list[StoryboardShot] = []
    for index, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            raise ValueError(
                f"Storyboard shot {index} for scene {scene.scene_number} is not a JSON object."
            )
        shot = StoryboardShot.from_dict(item, scene.scene_number, index)
        shot.shot_number = index
        shot.id = f"scene_{scene.scene_number:03d}_shot_{index:03d}"
        if not shot.image_prompt:
            shot.image_prompt = ", ".join(
                part
                for part in (
                    scene.heading,
                    shot.shot_type,
                    shot.subject,
                    shot.action,
                    shot.lighting,
                    shot.mood,
                )
                if part
            )
        shots.append(shot)
    return shots
