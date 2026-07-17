"""Screenplay generation panel."""

from __future__ import annotations

from nicegui import ui

from movie.storage import read_screenplay
from services.screenplay_service import ScreenplayService
from ui.panels.base_content_panel import BaseContentPanel


class ScreenplayPanel(BaseContentPanel[str]):
    title = "Screenplay"
    title_icon = "🎬"
    generate_label = "Generate Screenplay"
    generate_icon = "movie"
    select_message = "Select a project and generate the story first."
    missing_message = "No screenplay found. Generate the story first."
    generating_message = "AI Screenwriter is creating the screenplay..."
    success_notification = "Screenplay generated"

    def load_content(self, project_name: str) -> str:
        return read_screenplay(project_name)

    def generate_content(self, project_name: str) -> str:
        return ScreenplayService.generate(project_name)

    def render_content(self, content: str) -> None:
        self.output.clear()
        with self.output:
            with ui.card().classes("w-full shadow-none border"):
                ui.markdown(content).classes("w-full max-w-none font-mono")
