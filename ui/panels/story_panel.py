"""Story generation panel."""

from __future__ import annotations

from nicegui import ui

from movie.storage import read_story
from services.story_service import StoryService
from ui.panels.base_content_panel import BaseContentPanel


class StoryPanel(BaseContentPanel[str]):
    title = "Story"
    title_icon = "📖"
    generate_label = "Generate Story"
    generate_icon = "auto_awesome"
    select_message = "Select a project, then generate a story."
    missing_message = "No story found for this project."
    generating_message = "AI Writer is generating the story..."
    success_notification = "Story generated"

    def load_content(self, project_name: str) -> str:
        return read_story(project_name)

    def generate_content(self, project_name: str) -> str:
        return StoryService.generate(project_name)

    def render_content(self, content: str) -> None:
        self.output.clear()
        with self.output:
            with ui.card().classes("w-full shadow-none border"):
                ui.markdown(content).classes("w-full max-w-none")
