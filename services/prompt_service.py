"""Service facade for deterministic production prompt generation."""
from movie.prompt_builder import build_project_prompts
from movie.prompt_schema import PromptRecord
from movie.prompt_storage import load_latest_prompts
from movie.style_manager import StyleManager, VisualStyle


class PromptService:
    @staticmethod
    def generate(project_name: str, style_id: str | None = None) -> list[PromptRecord]:
        return build_project_prompts(project_name, style_id)

    @staticmethod
    def load(project_name: str) -> list[PromptRecord]:
        return load_latest_prompts(project_name)

    @staticmethod
    def styles() -> list[VisualStyle]:
        return StyleManager.list_styles()

    @staticmethod
    def project_style(project_name: str) -> str:
        return StyleManager.get_project_style(project_name)
