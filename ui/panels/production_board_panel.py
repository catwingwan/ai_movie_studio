"""Scene-centric production board."""
from __future__ import annotations

from nicegui import ui


class ProductionBoardPanel:
    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.studio = project_panel.studio

        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("🎬 Production Board").classes("text-2xl font-bold")
                ui.label("Track every scene from planned shots to approved production assets.").classes("text-sm text-gray-500")
            ui.button("Refresh", icon="refresh", on_click=self.refresh).props("outline")

        self.summary = ui.row().classes("w-full gap-3 flex-wrap")
        self.board = ui.column().classes("w-full gap-3")
        self.studio.events.subscribe("project.changed", lambda _: self.refresh())
        self.studio.events.subscribe("content.refreshed", lambda _: self.refresh())
        self.studio.events.subscribe("content.updated", lambda _: self.refresh())
        self.refresh()

    def _project(self) -> str | None:
        return self.studio.active_project or self.project_panel.selected_project

    @staticmethod
    def _metric(label: str, value: str, icon: str) -> None:
        with ui.card().classes("min-w-36 p-4 shadow-none border"):
            with ui.row().classes("items-center gap-2"):
                ui.icon(icon).classes("text-primary text-xl")
                with ui.column().classes("gap-0"):
                    ui.label(value).classes("text-xl font-bold")
                    ui.label(label).classes("text-xs text-gray-500")

    def refresh(self) -> None:
        project = self._project()
        self.summary.clear()
        self.board.clear()
        if not project:
            with self.board:
                ui.label("Select a project to view its production board.").classes("text-gray-500")
            return

        rows = self.studio.production_board.build(project)
        totals = self.studio.production_board.summary(project)
        minutes, seconds = divmod(totals["runtime_seconds"], 60)
        with self.summary:
            self._metric("Scenes", str(totals["scenes"]), "movie")
            self._metric("Shots", str(totals["shots"]), "photo_library")
            self._metric("Generated", str(totals["generated_images"]), "image")
            self._metric("Approved", str(totals["approved_images"]), "verified")
            self._metric("Runtime", f"{minutes}m {seconds:02d}s", "schedule")
            self._metric("Overall", f"{totals['progress'] * 100:.0f}%", "monitoring")

        with self.board:
            if not rows:
                ui.label("Generate scenes to start the production board.").classes("text-gray-500")
                return
            for scene in rows:
                state_style = {
                    "complete": ("Complete", "positive"),
                    "in_progress": ("In Production", "warning"),
                    "ready": ("Ready", "primary"),
                    "blocked": ("Needs Storyboard", "grey"),
                }[scene.state]
                with ui.card().classes("w-full p-4 shadow-none border"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("gap-0 min-w-0"):
                            ui.label(f"Scene {scene.scene_number:03d}").classes("text-xs text-gray-500")
                            ui.label(scene.heading).classes("font-semibold truncate")
                        ui.badge(state_style[0], color=state_style[1])
                    ui.linear_progress(value=scene.production_progress).classes("w-full mt-3")
                    with ui.row().classes("w-full gap-4 flex-wrap text-sm mt-2"):
                        ui.label(f"🎞 {scene.shots} shots")
                        ui.label(f"🧠 {scene.prompts}/{scene.shots} prompts")
                        ui.label(f"🖼 {scene.generated_images}/{scene.shots} images")
                        ui.label(f"✅ {scene.approved_images}/{scene.shots} approved")
                        ui.label(f"🎥 {scene.videos}/{scene.shots} videos")
                        ui.label(f"⏱ {scene.duration_seconds}s")
