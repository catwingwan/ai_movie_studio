"""Character generation panel."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from services.character_service import CharacterService
from ui.panels.base_content_panel import BaseContentPanel

CharacterList = list[dict[str, Any]]


class CharacterPanel(BaseContentPanel[CharacterList]):
    title = "Characters"
    title_icon = "🎭"
    generate_label = "Generate Characters"
    generate_icon = "groups"
    select_message = "Select a project, then generate characters."
    missing_message = "No characters generated yet."
    generating_message = "AI is creating the movie characters..."
    success_notification = "Characters generated"

    def load_content(self, project_name: str) -> CharacterList:
        return CharacterService.load(project_name)

    def generate_content(self, project_name: str) -> CharacterList:
        return CharacterService.generate(project_name)

    def loaded_message(self, content: CharacterList) -> str:
        return f"{len(content)} characters loaded."

    def generated_message(self, content: CharacterList) -> str:
        return f"{len(content)} characters generated successfully."

    def render_content(self, content: CharacterList) -> None:
        self.output.clear()
        with self.output:
            for character in content:
                with ui.card().classes("w-full shadow-none border"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(character.get("name", "Unnamed")).classes(
                            "text-lg font-bold"
                        )
                        role = character.get("role") or "Unspecified role"
                        ui.badge(str(role)).props("outline")

                    age = character.get("age")
                    if age not in (None, ""):
                        ui.label(f"Age: {age}").classes("text-sm text-gray-500")

                    if character.get("personality"):
                        ui.markdown(f"**Personality:** {character['personality']}")
                    if character.get("goal"):
                        ui.markdown(f"**Goal:** {character['goal']}")
                    if character.get("conflict"):
                        ui.markdown(f"**Conflict:** {character['conflict']}")
