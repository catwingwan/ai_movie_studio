"""ComfyUI-backed image generation workspace."""
from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path

from nicegui import ui

from movie.image_studio import PROFILES, ImageRecord, load_image_records
from movie.prompt_storage import load_latest_prompts
from movie.state import app_state
from services.image_service import ImageService
from services.comfyui_manager_service import ComfyUIManagerService
from services.job_queue import JobStatus, job_queue


class ImageStudioPanel:
    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.records: list[ImageRecord] = []

        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("🖼️ Image Studio").classes("text-2xl font-bold")
                ui.label("Generate cinematic frames from saved master prompts through local ComfyUI.").classes(
                    "text-sm text-gray-500"
                )
            ui.button("Refresh Gallery", icon="refresh", on_click=self.refresh).props("outline")

        with ui.card().classes("w-full shadow-none border rounded-xl"):
            with ui.row().classes("w-full items-end gap-3"):
                settings = ComfyUIManagerService.load_settings()
                initial_model = settings.checkpoint_name or None
                initial_model_options = (
                    {initial_model: initial_model}
                    if initial_model
                    else {}
                )
                self.model_select = ui.select(
                    initial_model_options,
                    value=initial_model,
                    label="Image Model",
                ).classes("w-72")
                self.model_select.on_value_change(self._model_changed)
                self.profile_select = ui.select(
                    {profile.id: profile.name for profile in PROFILES},
                    value="draft",
                    label="Generation Profile",
                ).classes("w-56")
                self.scene_select = ui.select({}, label="Scene").classes("w-40")
                self.shot_select = ui.select({}, label="Shot").classes("w-40")
                self.seed_input = ui.number("Seed (0 = random)", value=0, min=0, precision=0).classes("w-48")
                self.generate_button = ui.button("Generate New Version", icon="image", on_click=self.generate_shot)
                self.scene_button = ui.button("Generate Scene", icon="collections", on_click=self.generate_scene).props("outline")

            self.status = ui.label("Select a project with master prompts.").classes("text-sm text-gray-500")

        self.gallery = ui.column().classes("w-full gap-4")
        self.scene_select.on_value_change(self._scene_changed)
        app_state.on_project_changed(self.refresh)
        app_state.on_content_changed(self.refresh)
        self.refresh(app_state.active_project)

    @property
    def active_project(self) -> str | None:
        return app_state.active_project or getattr(self.project_panel, "selected_project", None)

    def _prompt_map(self):
        project = self.active_project
        return load_latest_prompts(project) if project else []

    def refresh(self, project_name: str | None = None) -> None:
        project = project_name or self.active_project
        try:
            report = ComfyUIManagerService.inspect_capabilities()
            model_options = {item: item for item in report.checkpoints}
            selected_model = report.selected_checkpoint
            if not selected_model and report.checkpoints:
                selected_model = report.checkpoints[0]
            if selected_model and selected_model not in model_options:
                model_options[selected_model] = selected_model
            self.model_select.set_options(
                model_options,
                value=selected_model,
            )
        except Exception:
            pass
        prompts = load_latest_prompts(project) if project else []
        scenes = sorted({item.scene_number for item in prompts})
        self.scene_select.options = {number: f"Scene {number:03d}" for number in scenes}
        if scenes and self.scene_select.value not in scenes:
            self.scene_select.value = scenes[0]
        self.scene_select.update()
        self._scene_changed(None)
        self.records = load_image_records(project) if project else []
        self._render_gallery()
        if not project:
            self.status.set_text("Select a project first.")
        elif not prompts:
            self.status.set_text("Build master prompts before generating images.")
        else:
            self.status.set_text(f"{len(prompts)} prompts ready · {len(self.records)} generated images")

    def _model_changed(self, _event) -> None:
        settings = ComfyUIManagerService.load_settings()
        settings.library_workflow_id = settings.library_workflow_id or "standard_checkpoint"
        settings.checkpoint_name = str(self.model_select.value or "")
        ComfyUIManagerService.save_settings(settings)

    def _scene_changed(self, _event) -> None:
        scene = int(self.scene_select.value or 0)
        shots = sorted(item.shot_number for item in self._prompt_map() if item.scene_number == scene)
        self.shot_select.options = {number: f"Shot {number:03d}" for number in shots}
        if shots and self.shot_select.value not in shots:
            self.shot_select.value = shots[0]
        self.shot_select.update()

    async def _wait_job(self, job_id: str, label: str):
        while True:
            job = job_queue.get(job_id)
            if job is None:
                raise RuntimeError("Image job disappeared from the queue.")
            if job.status is JobStatus.COMPLETED:
                return job.result
            if job.status is JobStatus.FAILED:
                raise RuntimeError(job.error or "Image generation failed.")
            if job.status is JobStatus.CANCELLED:
                raise RuntimeError("Image generation was cancelled.")
            self.status.set_text(f"{label}: {job.message.lower()}...")
            await asyncio.sleep(0.75)

    async def generate_shot(self) -> None:
        project = self.active_project
        scene = int(self.scene_select.value or 0)
        shot = int(self.shot_select.value or 0)
        prompt = next((p for p in self._prompt_map() if p.scene_number == scene and p.shot_number == shot), None)
        if not project or prompt is None:
            ui.notify("Select a project, scene, and shot with a saved prompt", type="warning")
            return
        self.generate_button.disable()
        try:
            seed = int(self.seed_input.value or 0) or None
            job_id = job_queue.submit(
                f"Generate Image S{scene:03d} SH{shot:03d}",
                ImageService.generate_shot,
                project,
                prompt,
                profile_id=str(self.profile_select.value or "draft"),
                checkpoint=str(self.model_select.value or "") or None,
                seed=seed,
                project_name=project,
            )
            self.status.set_text("Image queued in ComfyUI...")
            await self._wait_job(job_id, "Generating image")
            ui.notify("Image generated and downloaded", type="positive")
            app_state.notify_content_changed()
        except Exception as error:
            self.status.set_text("Image generation failed.")
            ui.notify(str(error), type="negative", multi_line=True)
        finally:
            self.generate_button.enable()

    async def generate_scene(self) -> None:
        project = self.active_project
        scene = int(self.scene_select.value or 0)
        if not project or scene <= 0:
            ui.notify("Select a project and scene", type="warning")
            return
        self.scene_button.disable()
        try:
            job_id = job_queue.submit(
                f"Generate Images Scene {scene:03d}",
                ImageService.generate_scene,
                project,
                scene,
                profile_id=str(self.profile_select.value or "draft"),
                checkpoint=str(self.model_select.value or "") or None,
                project_name=project,
            )
            self.status.set_text("Scene image batch queued...")
            results = await self._wait_job(job_id, "Generating scene images")
            count = len(results or [])
            ui.notify(f"Scene generation completed · {count} new image(s)", type="positive")
            app_state.notify_content_changed()
        except Exception as error:
            self.status.set_text("Scene image generation failed.")
            ui.notify(str(error), type="negative", multi_line=True)
        finally:
            self.scene_button.enable()

    def _render_gallery(self) -> None:
        self.gallery.clear()
        with self.gallery:
            if not self.records:
                ui.label("No generated images yet.").classes("text-sm text-gray-500")
                return
            grouped: dict[int, list[ImageRecord]] = {}
            for record in self.records:
                grouped.setdefault(record.scene_number, []).append(record)
            for scene_number, records in grouped.items():
                ui.label(f"Scene {scene_number:03d}").classes("text-xl font-bold")
                with ui.grid(columns=3).classes("w-full gap-4"):
                    for record in records:
                        project = self.active_project
                        image_path = (
                            Path("data/projects") / str(project) / "images"
                            / f"scene_{record.scene_number:03d}" / f"shot_{record.shot_number:03d}"
                            / record.filename
                        )
                        with ui.card().classes("shadow-none border rounded-xl"):
                            if image_path.exists():
                                ui.image(str(image_path)).classes("w-full rounded-lg")
                            ui.label(f"Shot {record.shot_number:03d}").classes("font-bold")
                            ui.label(f"Profile: {record.profile_id} · Seed: {record.seed}").classes(
                                "text-xs text-gray-500"
                            )
                            ui.label(f"Prompt v{record.prompt_version:03d}").classes("text-xs text-gray-500")
