"""Service-layer interface for storyboard generation and editing."""

from __future__ import annotations

from movie.storyboard import generate_storyboards, update_shot
from movie.storyboard_schema import SceneStoryboard, StoryboardShot
from movie.storyboard_storage import load_storyboards


class StoryboardService:
    @staticmethod
    def generate(project_name: str) -> list[SceneStoryboard]:
        return generate_storyboards(project_name, regenerate=False)

    @staticmethod
    def regenerate(project_name: str) -> list[SceneStoryboard]:
        return generate_storyboards(project_name, regenerate=True)

    @staticmethod
    def load(project_name: str) -> list[SceneStoryboard]:
        return load_storyboards(project_name)

    @staticmethod
    def save_shot(project_name: str, shot: StoryboardShot) -> None:
        update_shot(project_name, shot)
