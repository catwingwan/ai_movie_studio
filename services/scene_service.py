"""Service-layer access to the structured scene engine."""

from __future__ import annotations

from movie.scene import generate_scenes
from movie.scene_schema import Scene
from movie.scene_storage import load_scenes, save_scene


class SceneService:
    @staticmethod
    def generate(project_name: str) -> list[Scene]:
        return generate_scenes(project_name)

    @staticmethod
    def load(project_name: str) -> list[Scene]:
        return load_scenes(project_name)

    @staticmethod
    def save(project_name: str, scene: Scene) -> None:
        save_scene(project_name, scene)
