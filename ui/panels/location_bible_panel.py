"""Location Bible generation and editing workspace."""
from __future__ import annotations
from functools import partial
from nicegui import ui
from movie.location_bible_schema import LocationBible
from movie.state import app_state
from services.location_bible_service import LocationBibleService
from ui.panels.base_content_panel import BaseContentPanel

class LocationBiblePanel(BaseContentPanel[list[LocationBible]]):
    title = "Location Bible"
    title_icon = "🏠"
    generate_label = "Generate Location Bible"
    generate_icon = "location_city"
    missing_message = "No Location Bible yet. Generate scenes first."
    generating_message = "Building consistent visual profiles for each location..."
    success_notification = "Location Bible generated"

    def load_content(self, project_name: str) -> list[LocationBible]:
        return LocationBibleService.load(project_name)
    def generate_content(self, project_name: str) -> list[LocationBible]:
        return LocationBibleService.generate(project_name)
    def loaded_message(self, content: list[LocationBible]) -> str:
        return f"{len(content)} location profiles loaded."
    def generated_message(self, content: list[LocationBible]) -> str:
        return f"{len(content)} location profiles ready for image prompts."

    def _save(self, bible: LocationBible, fields: dict[str, object]) -> None:
        project = self.active_project
        if not project:
            return
        data = bible.to_dict()
        for key, widget in fields.items():
            value = getattr(widget, "value", "")
            if key in {"color_palette", "recurring_objects"}:
                data[key] = [item.strip() for item in str(value or "").split(",") if item.strip()]
            else:
                data[key] = str(value or "").strip()
        LocationBibleService.save(project, data)
        app_state.notify_content_changed()
        ui.notify(f"{bible.name} saved", type="positive")

    def render_content(self, content: list[LocationBible]) -> None:
        self.output.clear()
        with self.output:
            for bible in content:
                with ui.card().classes("w-full shadow-none border rounded-xl"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("gap-0"):
                            ui.label(bible.name).classes("text-xl font-bold")
                            ui.label(bible.type or "Production location").classes("text-sm text-gray-500")
                        ui.badge(bible.status.title()).props("outline color=primary")
                    fields: dict[str, object] = {}
                    with ui.expansion("Edit location identity", icon="edit").classes("w-full"):
                        with ui.grid(columns=2).classes("w-full gap-3"):
                            fields["type"] = ui.input("Type", value=bible.type)
                            fields["architecture"] = ui.input("Architecture", value=bible.architecture)
                            fields["layout"] = ui.input("Layout", value=bible.layout)
                            fields["lighting"] = ui.input("Lighting", value=bible.lighting)
                        fields["color_palette"] = ui.input("Color palette", value=", ".join(bible.color_palette)).classes("w-full")
                        fields["recurring_objects"] = ui.input("Recurring objects", value=", ".join(bible.recurring_objects)).classes("w-full")
                        fields["atmosphere"] = ui.textarea("Atmosphere", value=bible.atmosphere).classes("w-full")
                        fields["interior"] = ui.textarea("Interior", value=bible.interior).classes("w-full")
                        fields["exterior"] = ui.textarea("Exterior", value=bible.exterior).classes("w-full")
                        fields["consistency_prompt"] = ui.textarea("Consistency prompt", value=bible.consistency_prompt).classes("w-full")
                        fields["negative_prompt"] = ui.textarea("Negative prompt", value=bible.negative_prompt).classes("w-full")
                        ui.button("Save Location", icon="save", on_click=partial(self._save, bible, fields))
                    if bible.consistency_prompt:
                        ui.label("Consistency prompt").classes("text-xs uppercase tracking-wide text-gray-400")
                        ui.label(bible.consistency_prompt).classes("text-sm")
                    if bible.color_palette:
                        with ui.row().classes("gap-2 flex-wrap"):
                            for item in bible.color_palette:
                                ui.badge(item).props("outline")
