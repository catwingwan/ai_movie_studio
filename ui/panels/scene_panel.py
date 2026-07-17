"""Structured scene viewer and lightweight scene editor."""

from __future__ import annotations

from nicegui import ui

from movie.scene_schema import Scene
from movie.state import app_state
from services.scene_service import SceneService
from ui.panels.base_content_panel import BaseContentPanel

SceneList = list[Scene]


class ScenePanel(BaseContentPanel[SceneList]):
    title = "Scenes"
    title_icon = "🎞"
    generate_label = "Generate Scenes"
    generate_icon = "view_list"
    select_message = "Select a project first."
    missing_message = "No scenes generated yet."
    generating_message = "Local AI is breaking the screenplay into production scenes..."
    success_notification = "Scenes generated"

    def load_content(self, project_name: str) -> SceneList:
        return SceneService.load(project_name)

    def generate_content(self, project_name: str) -> SceneList:
        return SceneService.generate(project_name)

    def loaded_message(self, content: SceneList) -> str:
        return self._summary(content, "loaded")

    def generated_message(self, content: SceneList) -> str:
        return self._summary(content, "generated")

    @staticmethod
    def _summary(content: SceneList, verb: str) -> str:
        seconds = sum(scene.duration_seconds for scene in content)
        minutes, remainder = divmod(seconds, 60)
        return f"{len(content)} scenes {verb} · estimated runtime {minutes}m {remainder:02d}s."

    @staticmethod
    def _duration_label(seconds: int) -> str:
        minutes, remainder = divmod(max(0, seconds), 60)
        return f"{minutes}m {remainder:02d}s"

    def render_content(self, content: SceneList) -> None:
        self.output.clear()
        with self.output:
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(f"{len(content)} production scenes").classes("text-lg font-semibold")
                ui.badge(
                    f"Runtime {self._duration_label(sum(s.duration_seconds for s in content))}"
                ).props("outline color=primary")

            for scene in content:
                with ui.card().classes("w-full shadow-none border rounded-xl"):
                    with ui.row().classes("w-full items-start justify-between gap-4"):
                        with ui.column().classes("gap-1 flex-grow"):
                            ui.label(f"Scene {scene.scene_number:02d}").classes(
                                "text-xs font-bold uppercase tracking-wide text-blue-600"
                            )
                            ui.label(scene.heading).classes("text-xl font-bold")
                            details = " · ".join(
                                item for item in (scene.location, scene.time) if item
                            ) or "Location and time not specified"
                            ui.label(details).classes("text-sm text-gray-500")
                        ui.badge(self._duration_label(scene.duration_seconds)).props("outline")

                    if scene.characters:
                        with ui.row().classes("gap-1 flex-wrap"):
                            for character in scene.characters:
                                ui.badge(character).props("color=secondary outline")

                    if scene.summary:
                        ui.label("Summary").classes("text-xs font-bold uppercase text-gray-500 mt-2")
                        ui.markdown(scene.summary).classes("w-full")

                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button(
                            "Edit",
                            icon="edit",
                            on_click=lambda _, selected=scene: self.open_editor(selected),
                        ).props("flat")
                        ui.button("Storyboard", icon="photo_library").props("flat disable")

    def open_editor(self, scene: Scene) -> None:
        project = self.active_project
        if not project:
            ui.notify("Select a project first", type="warning")
            return

        with ui.dialog() as dialog, ui.card().classes("w-full max-w-3xl"):
            ui.label(f"Edit Scene {scene.scene_number:02d}").classes("text-xl font-bold")
            heading = ui.input("Scene heading", value=scene.heading).classes("w-full")
            with ui.row().classes("w-full gap-3"):
                location = ui.input("Location", value=scene.location).classes("flex-1")
                time = ui.input("Time", value=scene.time).classes("flex-1")
                duration = ui.number(
                    "Duration (seconds)", value=scene.duration_seconds, min=1
                ).classes("w-44")
            characters = ui.input(
                "Characters (comma-separated)", value=", ".join(scene.characters)
            ).classes("w-full")
            summary = ui.textarea("Summary", value=scene.summary).classes("w-full")
            action = ui.textarea("Action", value=scene.action).classes("w-full")

            def save_changes() -> None:
                scene.heading = (heading.value or "").strip() or f"SCENE {scene.scene_number}"
                scene.location = (location.value or "").strip()
                scene.time = (time.value or "").strip()
                scene.duration_seconds = max(1, int(duration.value or 1))
                scene.characters = [
                    item.strip() for item in (characters.value or "").split(",") if item.strip()
                ]
                scene.summary = (summary.value or "").strip()
                scene.action = (action.value or "").strip()
                SceneService.save(project, scene)
                dialog.close()
                app_state.notify_content_changed()
                ui.notify("Scene saved", type="positive")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Save Scene", icon="save", on_click=save_changes)

        dialog.open()
