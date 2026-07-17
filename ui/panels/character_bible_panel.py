"""Character Bible generation, preview, and editing workspace."""

from __future__ import annotations

from functools import partial

from nicegui import ui

from movie.character_bible_schema import CharacterBible
from movie.state import app_state
from services.character_bible_service import CharacterBibleService
from ui.panels.base_content_panel import BaseContentPanel


class CharacterBiblePanel(BaseContentPanel[list[CharacterBible]]):
    title = "Character Bible"
    title_icon = "👤"
    generate_label = "Generate Character Bible"
    generate_icon = "face_retouching_natural"
    missing_message = "No Character Bible yet. Generate characters first."
    generating_message = "Creating consistent visual profiles one character at a time..."
    success_notification = "Character Bible generated"

    def load_content(self, project_name: str) -> list[CharacterBible]:
        return CharacterBibleService.load(project_name)

    def generate_content(self, project_name: str) -> list[CharacterBible]:
        return CharacterBibleService.generate(project_name)

    def loaded_message(self, content: list[CharacterBible]) -> str:
        return f"{len(content)} character profiles loaded."

    def generated_message(self, content: list[CharacterBible]) -> str:
        return f"{len(content)} character profiles ready for image prompts."

    def _save(self, bible: CharacterBible, fields: dict[str, object]) -> None:
        project = self.active_project
        if not project:
            return
        data = bible.to_dict()
        for key, widget in fields.items():
            value = getattr(widget, "value", "")
            if key in {"default_wardrobe", "color_palette", "distinguishing_features"}:
                data[key] = [item.strip() for item in str(value or "").split(",") if item.strip()]
            else:
                data[key] = str(value or "").strip()
        CharacterBibleService.save(project, data)
        app_state.notify_content_changed()
        ui.notify(f"{bible.name} saved", type="positive")

    def render_content(self, content: list[CharacterBible]) -> None:
        self.output.clear()
        with self.output:
            for bible in content:
                with ui.card().classes("w-full shadow-none border rounded-xl"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("gap-0"):
                            ui.label(bible.name).classes("text-xl font-bold")
                            ui.label(" · ".join(filter(None, [bible.role, bible.age]))).classes(
                                "text-sm text-gray-500"
                            )
                        ui.badge(bible.status.title()).props("outline color=primary")

                    fields: dict[str, object] = {}
                    with ui.expansion("Edit visual identity", icon="edit").classes("w-full"):
                        with ui.grid(columns=2).classes("w-full gap-3"):
                            fields["face"] = ui.input("Face", value=bible.face)
                            fields["hair"] = ui.input("Hair", value=bible.hair)
                            fields["eyes"] = ui.input("Eyes", value=bible.eyes)
                            fields["skin_tone"] = ui.input("Skin tone", value=bible.skin_tone)
                            fields["body_type"] = ui.input("Body type", value=bible.body_type)
                            fields["height"] = ui.input("Height", value=bible.height)
                        fields["distinguishing_features"] = ui.input(
                            "Distinguishing features (comma separated)",
                            value=", ".join(bible.distinguishing_features),
                        ).classes("w-full")
                        fields["default_wardrobe"] = ui.input(
                            "Default wardrobe (comma separated)",
                            value=", ".join(bible.default_wardrobe),
                        ).classes("w-full")
                        fields["color_palette"] = ui.input(
                            "Color palette (comma separated)",
                            value=", ".join(bible.color_palette),
                        ).classes("w-full")
                        fields["consistency_prompt"] = ui.textarea(
                            "Consistency prompt", value=bible.consistency_prompt
                        ).classes("w-full")
                        fields["negative_prompt"] = ui.textarea(
                            "Negative prompt", value=bible.negative_prompt
                        ).classes("w-full")
                        ui.button(
                            "Save Profile",
                            icon="save",
                            on_click=partial(self._save, bible, fields),
                        )

                    if bible.consistency_prompt:
                        ui.label("Consistency prompt").classes(
                            "text-xs uppercase tracking-wide text-gray-400"
                        )
                        ui.label(bible.consistency_prompt).classes("text-sm")
                    if bible.default_wardrobe:
                        with ui.row().classes("gap-2 flex-wrap"):
                            for item in bible.default_wardrobe:
                                ui.badge(item).props("outline")
