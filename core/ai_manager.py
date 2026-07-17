"""Unified, lazy-loaded AI façade for local text and image services."""
from __future__ import annotations


class AIManager:
    """Keep UI independent of concrete AI providers and avoid eager imports."""

    def generate_characters(self, project: str):
        from services.character_service import CharacterService
        return CharacterService.generate(project)

    def generate_story(self, project: str):
        from services.story_service import StoryService
        return StoryService.generate(project)

    def generate_screenplay(self, project: str):
        from services.screenplay_service import ScreenplayService
        return ScreenplayService.generate(project)

    def generate_scenes(self, project: str):
        from services.scene_service import SceneService
        return SceneService.generate(project)

    def generate_storyboard(self, project: str):
        from services.storyboard_service import StoryboardService
        return StoryboardService.generate(project)

    def review_direction(self, project: str):
        from services.director_service import DirectorService
        return DirectorService.generate(project)

    def generate_locations(self, project: str):
        from services.location_bible_service import LocationBibleService
        return LocationBibleService.generate(project)

    def generate_props(self, project: str):
        from services.prop_library_service import PropLibraryService
        return PropLibraryService.generate(project)

    def build_prompts(self, project: str, style_id: str | None = None):
        from services.prompt_service import PromptService
        return PromptService.generate(project, style_id)

    def generate_image(self, project: str, scene_number: int, shot_number: int, **options):
        from services.image_service import ImageService
        return ImageService.generate_shot(project, scene_number, shot_number, **options)
