"""Storyboard workspace for scene-to-shot generation and shot editing."""

from __future__ import annotations

from nicegui import ui

from movie.state import app_state
from movie.storyboard_schema import SceneStoryboard, StoryboardShot
from services.storyboard_service import StoryboardService
from ui.panels.base_content_panel import BaseContentPanel

StoryboardList = list[SceneStoryboard]


class StoryboardPanel(BaseContentPanel[StoryboardList]):
    title = "Storyboard"
    title_icon = "🎥"
    generate_label = "Generate Storyboard"
    generate_icon = "photo_library"
    select_message = "Select a project first."
    missing_message = "No storyboard generated yet. Generate scenes first."
    generating_message = "Local AI is directing scenes into cinematic shots..."
    success_notification = "Storyboard generated"

    def load_content(self, project_name: str) -> StoryboardList:
        return StoryboardService.load(project_name)

    def generate_content(self, project_name: str) -> StoryboardList:
        return StoryboardService.generate(project_name)

    def loaded_message(self, content: StoryboardList) -> str:
        return self._summary(content, "loaded")

    def generated_message(self, content: StoryboardList) -> str:
        return self._summary(content, "generated")

    @staticmethod
    def _summary(content: StoryboardList, verb: str) -> str:
        shots = sum(len(item.shots) for item in content)
        seconds = sum(item.duration_seconds for item in content)
        minutes, remainder = divmod(seconds, 60)
        return (
            f"{shots} shots across {len(content)} scenes {verb} · "
            f"estimated visual runtime {minutes}m {remainder:02d}s."
        )

    @staticmethod
    def _duration_label(seconds: int) -> str:
        minutes, remainder = divmod(max(0, seconds), 60)
        return f"{minutes}m {remainder:02d}s"

    def render_content(self, content: StoryboardList) -> None:
        self.output.clear()
        total_shots = sum(len(item.shots) for item in content)
        total_seconds = sum(item.duration_seconds for item in content)

        with self.output:
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(
                    f"{len(content)} scenes · {total_shots} storyboard shots"
                ).classes("text-lg font-semibold")
                ui.badge(
                    f"Runtime {self._duration_label(total_seconds)}"
                ).props("outline color=primary")

            for storyboard in content:
                with ui.card().classes("w-full shadow-none border rounded-xl"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("gap-0"):
                            ui.label(f"Scene {storyboard.scene_number:02d}").classes(
                                "text-xs font-bold uppercase tracking-wide text-blue-600"
                            )
                            ui.label(storyboard.scene_heading).classes("text-xl font-bold")
                        ui.badge(
                            f"{len(storyboard.shots)} shots · "
                            f"{self._duration_label(storyboard.duration_seconds)}"
                        ).props("outline")

                    with ui.column().classes("w-full gap-2"):
                        for shot in storyboard.shots:
                            self._render_shot(shot)

    def _render_shot(self, shot: StoryboardShot) -> None:
        with ui.card().classes("w-full bg-slate-50 shadow-none border"):
            with ui.row().classes("w-full items-start justify-between gap-4"):
                with ui.column().classes("gap-1 flex-grow"):
                    ui.label(f"Shot {shot.shot_number:02d} · {shot.shot_type}").classes(
                        "font-bold"
                    )
                    ui.label(
                        " · ".join(
                            part
                            for part in (
                                shot.camera_angle,
                                shot.lens,
                                shot.movement,
                                shot.composition,
                            )
                            if part
                        )
                    ).classes("text-sm text-gray-500")
                ui.badge(f"{shot.duration_seconds}s").props("outline")

            if shot.subject or shot.action:
                ui.label(" — ".join(part for part in (shot.subject, shot.action) if part)).classes(
                    "text-sm"
                )

            with ui.row().classes("gap-1 flex-wrap"):
                if shot.lighting:
                    ui.badge(shot.lighting).props("outline color=amber")
                if shot.mood:
                    ui.badge(shot.mood).props("outline color=secondary")

            if shot.image_prompt:
                with ui.expansion("Image prompt", icon="image").classes("w-full"):
                    ui.markdown(shot.image_prompt).classes("text-sm")
                    if shot.negative_prompt:
                        ui.label("Negative prompt").classes(
                            "text-xs font-bold uppercase text-gray-500 mt-2"
                        )
                        ui.markdown(shot.negative_prompt).classes("text-sm")

            with ui.row().classes("w-full justify-end"):
                ui.button(
                    "Edit Shot",
                    icon="edit",
                    on_click=lambda _, selected=shot: self.open_editor(selected),
                ).props("flat")

    def open_editor(self, shot: StoryboardShot) -> None:
        project = self.active_project
        if not project:
            ui.notify("Select a project first", type="warning")
            return

        with ui.dialog() as dialog, ui.card().classes("w-full max-w-4xl"):
            ui.label(
                f"Edit Scene {shot.scene_number:02d} · Shot {shot.shot_number:02d}"
            ).classes("text-xl font-bold")

            with ui.row().classes("w-full gap-3"):
                shot_type = ui.input("Shot type", value=shot.shot_type).classes("flex-1")
                camera_angle = ui.input(
                    "Camera angle", value=shot.camera_angle
                ).classes("flex-1")
                lens = ui.input("Lens", value=shot.lens).classes("w-32")

            with ui.row().classes("w-full gap-3"):
                movement = ui.input("Movement", value=shot.movement).classes("flex-1")
                composition = ui.input(
                    "Composition", value=shot.composition
                ).classes("flex-1")
                duration = ui.number(
                    "Duration (seconds)", value=shot.duration_seconds, min=1, max=30
                ).classes("w-44")

            with ui.row().classes("w-full gap-3"):
                lighting = ui.input("Lighting", value=shot.lighting).classes("flex-1")
                mood = ui.input("Mood", value=shot.mood).classes("flex-1")

            subject = ui.input("Subject", value=shot.subject).classes("w-full")
            action = ui.textarea("Action", value=shot.action).classes("w-full")
            image_prompt = ui.textarea(
                "Image prompt", value=shot.image_prompt
            ).classes("w-full")
            negative_prompt = ui.textarea(
                "Negative prompt", value=shot.negative_prompt
            ).classes("w-full")

            def save_changes() -> None:
                shot.shot_type = (shot_type.value or "").strip() or "Medium Shot"
                shot.camera_angle = (camera_angle.value or "").strip() or "Eye Level"
                shot.lens = (lens.value or "").strip() or "50mm"
                shot.movement = (movement.value or "").strip() or "Static"
                shot.composition = (composition.value or "").strip() or "Rule of Thirds"
                shot.duration_seconds = max(1, min(30, int(duration.value or 4)))
                shot.lighting = (lighting.value or "").strip() or "Natural"
                shot.mood = (mood.value or "").strip() or "Neutral"
                shot.subject = (subject.value or "").strip()
                shot.action = (action.value or "").strip()
                shot.image_prompt = (image_prompt.value or "").strip()
                shot.negative_prompt = (negative_prompt.value or "").strip()
                StoryboardService.save_shot(project, shot)
                dialog.close()
                app_state.notify_content_changed()
                ui.notify("Storyboard shot saved", type="positive")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button("Save Shot", icon="save", on_click=save_changes)

        dialog.open()
