"""Production pipeline status and one-click text pipeline runner."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Callable

from nicegui import ui

from movie.project_manager import PROJECT_ROOT
from movie.production_manager import ProductionManager
from movie.state import app_state
from services.character_service import CharacterService
from services.job_queue import JobStatus, job_queue
from services.scene_service import SceneService
from services.screenplay_service import ScreenplayService
from services.story_service import StoryService


class PipelinePanel:
    """Display production progress and run the core movie-writing pipeline."""

    CORE_STAGE_NAMES = ("Characters", "Story", "Screenplay", "Scenes")

    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.is_running = False

        ui.label("🎬 Pipeline").classes("text-xl font-bold mt-4")

        self.project_name_label = ui.label("Select a project").classes(
            "text-sm text-gray-500"
        )

        self.container = ui.column().classes("w-full gap-2")

        with ui.row().classes("w-full gap-2"):
            self.run_button = ui.button(
                "Generate Movie Script",
                icon="play_arrow",
                on_click=self.run_pipeline,
            ).classes("flex-1")

            ui.button(
                icon="refresh",
                on_click=self.refresh,
            ).props("flat round").tooltip("Refresh progress")

        self.run_status = ui.label(
            "Select a project to start the pipeline."
        ).classes("text-sm text-gray-500")

        self.activity = ui.column().classes("w-full gap-1")

        app_state.on_project_changed(self.on_project_changed)
        app_state.on_content_changed(self.on_project_changed)

        self.refresh()

    def on_project_changed(self, project_name: str | None) -> None:
        if not self.is_running:
            self.refresh()

    @staticmethod
    def _file_has_content(path: Path) -> bool:
        return path.exists() and path.stat().st_size > 0

    @staticmethod
    def _characters_exist(path: Path) -> bool:
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return isinstance(data, list) and len(data) > 0
        except (json.JSONDecodeError, OSError):
            return False

    @staticmethod
    def _folder_has_files(path: Path, pattern: str = "*") -> bool:
        return path.exists() and any(item.is_file() for item in path.glob(pattern))

    def get_statuses(self, project_name: str) -> list[tuple[str, bool]]:
        status = ProductionManager.get_status(project_name)
        return [(label, status.get(label, False)) for label in ProductionManager.STAGES]

    def _core_statuses(self, project_name: str) -> dict[str, bool]:
        return {
            label: complete
            for label, complete in self.get_statuses(project_name)
            if label in self.CORE_STAGE_NAMES
        }

    def _next_pending_stage(self, project_name: str) -> str | None:
        statuses = self._core_statuses(project_name)
        return next(
            (name for name in self.CORE_STAGE_NAMES if not statuses.get(name, False)),
            None,
        )

    def _update_run_button(self, project_name: str | None) -> None:
        if self.is_running:
            self.run_button.set_text("Pipeline Running...")
            self.run_button.disable()
            return

        self.run_button.enable()

        if not project_name:
            self.run_button.set_text("Generate Movie Script")
            return

        next_stage = self._next_pending_stage(project_name)
        if next_stage is None:
            self.run_button.set_text("Movie Script Complete")
            self.run_button.disable()
        elif next_stage == "Characters":
            self.run_button.set_text("Generate Movie Script")
        else:
            self.run_button.set_text(f"Continue from {next_stage}")

    def refresh(self) -> None:
        self.container.clear()

        project_name = app_state.active_project or self.project_panel.selected_project
        self._update_run_button(project_name)

        if not project_name:
            self.project_name_label.set_text("Select a project")
            if not self.is_running:
                self.run_status.set_text("Select a project to start the pipeline.")

            with self.container:
                ui.label("No production progress available").classes(
                    "text-sm text-gray-500"
                )
            return

        self.project_name_label.set_text(project_name)

        statuses = self.get_statuses(project_name)
        completed = sum(1 for _, status in statuses if status)
        total = len(statuses)
        percentage = completed / total if total else 0

        if not self.is_running:
            next_stage = self._next_pending_stage(project_name)
            if next_stage:
                self.run_status.set_text(f"Next text stage: {next_stage}")
            else:
                self.run_status.set_text("Core movie script pipeline is complete.")

        with self.container:
            ui.linear_progress(value=percentage).classes("w-full")
            ui.label(f"{completed} of {total} stages complete").classes(
                "text-sm text-gray-500"
            )

            try:
                stats = ProductionManager.get_statistics(project_name)
                if stats.scenes:
                    minutes, seconds = divmod(stats.runtime_seconds, 60)
                    ui.label(
                        f"{stats.scenes} scenes · estimated runtime {minutes}m {seconds:02d}s"
                    ).classes("text-sm text-gray-500")
                if stats.shots:
                    ui.label(f"{stats.shots} storyboard shots ready").classes(
                        "text-sm text-gray-500"
                    )
                if stats.director_reviews:
                    ui.label(
                        f"{stats.director_reviews} Director AI reviews ready"
                    ).classes("text-sm text-gray-500")
                if stats.character_assets or stats.location_assets or stats.prop_assets:
                    ui.label(
                        f"Assets: {stats.character_assets} characters · "
                        f"{stats.location_assets} locations · {stats.prop_assets} props"
                    ).classes("text-sm text-gray-500")
            except Exception:
                pass

            for label, complete in statuses:
                with ui.row().classes("w-full items-center gap-2"):
                    ui.icon(
                        "check_circle" if complete else "radio_button_unchecked"
                    ).classes("text-green-600" if complete else "text-gray-400")
                    ui.label(label).classes(
                        "font-medium" if complete else "text-gray-500"
                    )

    def _add_activity(self, message: str, kind: str = "info") -> None:
        icon = {
            "running": "hourglass_top",
            "success": "check_circle",
            "error": "error",
            "skip": "skip_next",
            "info": "info",
        }.get(kind, "info")
        css = {
            "running": "text-blue-600",
            "success": "text-green-600",
            "error": "text-red-600",
            "skip": "text-gray-500",
            "info": "text-gray-500",
        }.get(kind, "text-gray-500")

        with self.activity:
            with ui.row().classes("items-center gap-2"):
                ui.icon(icon).classes(css)
                ui.label(message).classes("text-sm")

    @staticmethod
    def _stage_functions() -> dict[str, Callable[[str], object]]:
        return {
            "Characters": CharacterService.generate,
            "Story": StoryService.generate,
            "Screenplay": ScreenplayService.generate,
            "Scenes": SceneService.generate,
        }

    async def run_pipeline(self) -> None:
        """Generate only missing core stages and stop safely on the first error."""

        if self.is_running:
            return

        project_name = app_state.active_project or self.project_panel.selected_project
        if not project_name:
            ui.notify("Select a project first", type="warning")
            return

        project_file = PROJECT_ROOT / project_name / "project.json"
        if not self._file_has_content(project_file):
            ui.notify("The selected project is invalid or missing project.json", type="negative")
            return

        self.is_running = True
        self.activity.clear()
        self._update_run_button(project_name)
        self.run_status.set_text("Starting local AI movie-script pipeline...")

        stage_functions = self._stage_functions()

        try:
            for stage_name in self.CORE_STAGE_NAMES:
                if self._core_statuses(project_name).get(stage_name, False):
                    self._add_activity(f"{stage_name}: already complete", "skip")
                    continue

                self.run_status.set_text(f"Generating {stage_name} with local AI...")
                self._add_activity(f"{stage_name}: generating", "running")

                try:
                    job_id = job_queue.submit(
                        f"Generate {stage_name}",
                        stage_functions[stage_name],
                        project_name,
                        project_name=project_name,
                    )
                    while True:
                        job = job_queue.get(job_id)
                        if job is None:
                            raise RuntimeError("Pipeline job disappeared from the queue.")
                        if job.status is JobStatus.COMPLETED:
                            break
                        if job.status is JobStatus.FAILED:
                            raise RuntimeError(job.error or f"{stage_name} failed.")
                        if job.status is JobStatus.CANCELLED:
                            raise RuntimeError(f"{stage_name} job was cancelled.")
                        await asyncio.sleep(0.5)
                except Exception as error:
                    self._add_activity(f"{stage_name}: failed — {error}", "error")
                    self.run_status.set_text(
                        f"Pipeline stopped at {stage_name}. Fix the error, then continue."
                    )
                    ui.notify(
                        f"{stage_name} generation failed: {error}",
                        type="negative",
                        multi_line=True,
                    )
                    return

                self._add_activity(f"{stage_name}: complete", "success")
                app_state.notify_content_changed()
                self.refresh()
                await asyncio.sleep(0)

            self.run_status.set_text("Core movie script pipeline completed successfully.")
            ui.notify("Movie script pipeline completed", type="positive")

        finally:
            self.is_running = False
            app_state.notify_content_changed()
            self.refresh()
