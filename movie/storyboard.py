"""Storyboard engine orchestration with incremental scene-level persistence."""

from __future__ import annotations

from movie.scene_storage import load_scenes
from movie.storyboard_ai import generate_scene_shots
from movie.storyboard_schema import SceneStoryboard, StoryboardShot
from movie.storyboard_storage import (
    load_scene_shots,
    load_storyboards,
    replace_scene_shots,
    save_shot,
)


def generate_storyboards(project_name: str, regenerate: bool = False) -> list[SceneStoryboard]:
    if not project_name.strip():
        raise ValueError("No project selected.")

    scenes = load_scenes(project_name)
    if not scenes:
        raise FileNotFoundError("Generate scenes before generating the storyboard.")

    for scene in scenes:
        existing = load_scene_shots(project_name, scene.scene_number)
        if existing and not regenerate:
            continue
        shots = generate_scene_shots(scene)
        replace_scene_shots(project_name, scene.scene_number, shots)

    storyboards = load_storyboards(project_name)
    if not storyboards:
        raise RuntimeError("No storyboard shots were generated.")
    return storyboards


def update_shot(project_name: str, shot: StoryboardShot) -> None:
    save_shot(project_name, shot)
