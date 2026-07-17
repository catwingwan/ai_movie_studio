"""Prop Library generation and editing workspace."""
from __future__ import annotations
from functools import partial
from nicegui import ui
from movie.prop_schema import PropAsset
from movie.state import app_state
from services.prop_library_service import PropLibraryService
from ui.panels.base_content_panel import BaseContentPanel

class PropLibraryPanel(BaseContentPanel[list[PropAsset]]):
    title = "Prop Library"
    title_icon = "🎒"
    generate_label = "Generate Prop Library"
    generate_icon = "category"
    missing_message = "No props identified yet. Generate scenes first."
    generating_message = "Identifying continuity-critical props scene by scene..."
    success_notification = "Prop Library generated"

    def load_content(self, project_name: str) -> list[PropAsset]:
        return PropLibraryService.load(project_name)
    def generate_content(self, project_name: str) -> list[PropAsset]:
        return PropLibraryService.generate(project_name)
    def loaded_message(self, content: list[PropAsset]) -> str:
        return f"{len(content)} props loaded."
    def generated_message(self, content: list[PropAsset]) -> str:
        return f"{len(content)} continuity props ready."

    def _save(self, prop: PropAsset, fields: dict[str, object]) -> None:
        project = self.active_project
        if not project:
            return
        data = prop.to_dict()
        for key, widget in fields.items():
            value = getattr(widget, "value", "")
            if key in {"materials", "colors"}:
                data[key] = [item.strip() for item in str(value or "").split(",") if item.strip()]
            elif key == "scenes":
                data[key] = [int(item.strip()) for item in str(value or "").split(",") if item.strip().isdigit()]
            else:
                data[key] = str(value or "").strip()
        PropLibraryService.save(project, data)
        app_state.notify_content_changed()
        ui.notify(f"{prop.name} saved", type="positive")

    def render_content(self, content: list[PropAsset]) -> None:
        self.output.clear()
        with self.output:
            for prop in content:
                with ui.card().classes("w-full shadow-none border rounded-xl"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("gap-0"):
                            ui.label(prop.name).classes("text-xl font-bold")
                            ui.label(prop.category or "Production prop").classes("text-sm text-gray-500")
                        ui.badge(prop.status.title()).props("outline color=primary")
                    if prop.description:
                        ui.label(prop.description).classes("text-sm")
                    with ui.expansion("Edit prop continuity", icon="edit").classes("w-full"):
                        fields: dict[str, object] = {}
                        with ui.grid(columns=2).classes("w-full gap-3"):
                            fields["category"] = ui.input("Category", value=prop.category)
                            fields["condition"] = ui.input("Condition", value=prop.condition)
                            fields["materials"] = ui.input("Materials", value=", ".join(prop.materials))
                            fields["colors"] = ui.input("Colors", value=", ".join(prop.colors))
                        fields["scenes"] = ui.input("Scenes", value=", ".join(str(v) for v in prop.scenes)).classes("w-full")
                        fields["description"] = ui.textarea("Description", value=prop.description).classes("w-full")
                        fields["story_function"] = ui.textarea("Story function", value=prop.story_function).classes("w-full")
                        fields["consistency_prompt"] = ui.textarea("Consistency prompt", value=prop.consistency_prompt).classes("w-full")
                        fields["negative_prompt"] = ui.textarea("Negative prompt", value=prop.negative_prompt).classes("w-full")
                        ui.button("Save Prop", icon="save", on_click=partial(self._save, prop, fields))
                    with ui.row().classes("gap-2 flex-wrap"):
                        for scene in prop.scenes:
                            ui.badge(f"Scene {scene}").props("outline")
