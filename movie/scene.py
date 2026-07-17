"""Scene-engine orchestration."""

from __future__ import annotations

from movie.scene_ai import extract_scenes
from movie.scene_schema import Scene
from movie.scene_storage import replace_scenes
from movie.storage import read_screenplay


def generate_scenes(project_name: str) -> list[Scene]:
    if not project_name.strip():
        raise ValueError("No project selected.")

    screenplay = read_screenplay(project_name).strip()
    if not screenplay:
        raise FileNotFoundError("Generate the screenplay before generating scenes.")

    scenes = extract_scenes(screenplay)
    replace_scenes(project_name, scenes)
    return scenes
