"""Versioned production image asset workspace."""
from __future__ import annotations

import asyncio
from functools import partial

from nicegui import ui

from movie.asset_database import AssetDatabase, ImageAssetVersion
from movie.prompt_storage import load_latest_prompts
from movie.state import app_state
from services.image_asset_service import ImageAssetService
from services.image_service import ImageService
from services.job_queue import JobStatus, job_queue


STATUS_LABELS = {
    "draft": "Draft",
    "review": "In Review",
    "approved": "Approved",
    "rejected": "Rejected",
    "archived": "Archived",
}


class ImageAssetsPanel:
    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.items: list[ImageAssetVersion] = []

        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("🎞️ Image Assets").classes("text-2xl font-bold")
                ui.label("Review versions, approve production frames, and preserve every generation.").classes(
                    "text-sm text-gray-500"
                )
            ui.button("Refresh", icon="refresh", on_click=self.refresh).props("outline")

        with ui.row().classes("w-full gap-3 items-end"):
            self.search = ui.input("Search notes, tags, or checkpoint").props("clearable").classes("w-80")
            self.status_filter = ui.select(
                {"all": "All statuses", **STATUS_LABELS}, value="all", label="Status"
            ).classes("w-48")
            self.scene_filter = ui.select({"all": "All scenes"}, value="all", label="Scene").classes("w-40")
            ui.button("Apply", icon="filter_alt", on_click=self.refresh).props("outline")

        self.summary_row = ui.row().classes("w-full gap-3")
        self.status = ui.label("Select a project.").classes("text-sm text-gray-500")
        self.gallery = ui.column().classes("w-full gap-5")

        app_state.on_project_changed(self.refresh)
        app_state.on_content_changed(self.refresh)
        self.refresh(app_state.active_project)

    @property
    def active_project(self) -> str | None:
        return app_state.active_project or getattr(self.project_panel, "selected_project", None)

    def refresh(self, project_name: str | None = None) -> None:
        project = project_name or self.active_project
        self.gallery.clear()
        self.summary_row.clear()
        if not project:
            self.items = []
            self.status.set_text("Select a project first.")
            return
        database = AssetDatabase(project)
        all_items = database.list_versions()
        scenes = sorted({item.scene_number for item in all_items})
        scene_options = {"all": "All scenes", **{str(number): f"Scene {number:03d}" for number in scenes}}
        current_scene = str(self.scene_filter.value or "all")
        self.scene_filter.set_options(scene_options, value=current_scene if current_scene in scene_options else "all")
        selected_scene = None if self.scene_filter.value == "all" else int(self.scene_filter.value)
        self.items = database.list_versions(
            scene_number=selected_scene,
            status=str(self.status_filter.value or "all"),
            query=str(self.search.value or ""),
        )
        summary = database.summary()
        self._render_summary(summary)
        self._render_gallery(project)
        self.status.set_text(
            f"{summary['assets']} shot asset(s) · {summary['versions']} version(s) · "
            f"{summary['approved']} approved"
        )

    def _render_summary(self, summary: dict[str, int]) -> None:
        with self.summary_row:
            for label, key in (("Shot Assets", "assets"), ("Versions", "versions"),
                               ("In Review", "review"), ("Approved", "approved"),
                               ("Rejected", "rejected")):
                with ui.card().classes("shadow-none border rounded-xl px-5 py-3 min-w-32"):
                    ui.label(str(summary[key])).classes("text-2xl font-bold")
                    ui.label(label).classes("text-xs text-gray-500")

    def _render_gallery(self, project: str) -> None:
        with self.gallery:
            if not self.items:
                ui.label("No image asset versions match the current filters.").classes("text-sm text-gray-500")
                return
            grouped: dict[tuple[int, int], list[ImageAssetVersion]] = {}
            for item in self.items:
                grouped.setdefault((item.scene_number, item.shot_number), []).append(item)
            for (scene, shot), versions in grouped.items():
                with ui.row().classes("w-full items-center justify-between"):
                    ui.label(f"Scene {scene:03d} · Shot {shot:03d}").classes("text-xl font-bold")
                    ui.button(
                        "Compare Versions", icon="compare", on_click=partial(self._show_compare, versions)
                    ).props("flat")
                with ui.grid(columns=3).classes("w-full gap-4"):
                    for item in versions:
                        self._render_card(project, item)

    def _render_card(self, project: str, item: ImageAssetVersion) -> None:
        path = AssetDatabase(project).image_path(item)
        with ui.card().classes("shadow-none border rounded-xl"):
            if path.exists():
                ui.image(str(path)).classes("w-full rounded-lg")
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(f"Version {item.version:03d}").classes("font-bold")
                ui.badge(STATUS_LABELS.get(item.status, item.status))
            ui.label(f"{'★' * item.rating}{'☆' * (5 - item.rating)}").classes("text-amber-600")
            ui.label(f"{item.profile_id} · Seed {item.seed}").classes("text-xs text-gray-500")
            ui.label(item.checkpoint or "No checkpoint metadata").classes("text-xs text-gray-500 truncate")
            if item.notes:
                ui.label(item.notes).classes("text-sm line-clamp-2")
            if item.tags:
                with ui.row().classes("gap-1"):
                    for tag in item.tags[:5]:
                        ui.badge(tag).props("outline")
            with ui.row().classes("w-full gap-1 flex-wrap"):
                ui.button("Approve", icon="check", on_click=partial(self._set_status, item, "approved")).props("flat color=positive")
                ui.button("Reject", icon="close", on_click=partial(self._set_status, item, "rejected")).props("flat color=negative")
                ui.button("Review", icon="rate_review", on_click=partial(self._edit_review, item)).props("flat")
                ui.button("Metadata", icon="info", on_click=partial(self._show_metadata, item)).props("flat")
                ui.button("New Version", icon="autorenew", on_click=partial(self.generate_new_version, item)).props("outline")

    def _set_status(self, item: ImageAssetVersion, status: str) -> None:
        project = self.active_project
        if not project:
            return
        ImageAssetService.update_review(project, item.asset_id, item.version, status=status)
        ui.notify(f"Version {item.version:03d} marked {STATUS_LABELS[status].lower()}", type="positive")
        self.refresh(project)

    def _edit_review(self, item: ImageAssetVersion) -> None:
        project = self.active_project
        if not project:
            return
        with ui.dialog() as dialog, ui.card().classes("w-[42rem] max-w-full"):
            ui.label(f"Review {item.asset_id} · v{item.version:03d}").classes("text-xl font-bold")
            rating = ui.slider(min=0, max=5, value=item.rating).props("label-always")
            notes = ui.textarea("Director notes", value=item.notes).classes("w-full")
            tags = ui.input("Tags (comma separated)", value=", ".join(item.tags or [])).classes("w-full")
            status = ui.select(STATUS_LABELS, value=item.status, label="Workflow status").classes("w-full")
            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                def save() -> None:
                    ImageAssetService.update_review(
                        project, item.asset_id, item.version,
                        status=str(status.value), rating=int(rating.value or 0),
                        notes=str(notes.value or ""),
                        tags=[part.strip() for part in str(tags.value or "").split(",")],
                    )
                    dialog.close()
                    self.refresh(project)
                    ui.notify("Asset review saved", type="positive")
                ui.button("Save Review", icon="save", on_click=save)
        dialog.open()

    def _show_metadata(self, item: ImageAssetVersion) -> None:
        with ui.dialog() as dialog, ui.card().classes("w-[44rem] max-w-full"):
            ui.label(f"{item.asset_id} · Version {item.version:03d}").classes("text-xl font-bold")
            rows = {
                "Status": STATUS_LABELS.get(item.status, item.status), "Rating": item.rating,
                "Checkpoint": item.checkpoint, "Workflow": item.workflow_name,
                "Profile": item.profile_id, "Seed": item.seed,
                "Prompt version": item.prompt_version, "ComfyUI prompt ID": item.prompt_id,
                "Generated": item.generated_at, "File": item.filename,
            }
            for label, value in rows.items():
                with ui.row().classes("w-full gap-3"):
                    ui.label(label).classes("w-36 font-medium")
                    ui.label(str(value or "—")).classes("text-sm break-all")
            ui.button("Close", on_click=dialog.close).props("flat")
        dialog.open()

    def _show_compare(self, versions: list[ImageAssetVersion]) -> None:
        project = self.active_project
        if not project:
            return
        selected = sorted(versions, key=lambda item: item.version, reverse=True)[:2]
        with ui.dialog() as dialog, ui.card().classes("w-[70rem] max-w-full"):
            ui.label("Compare Image Versions").classes("text-xl font-bold")
            with ui.grid(columns=max(1, len(selected))).classes("w-full gap-4"):
                for item in selected:
                    with ui.card().classes("shadow-none border"):
                        path = AssetDatabase(project).image_path(item)
                        if path.exists():
                            ui.image(str(path)).classes("w-full rounded-lg")
                        ui.label(f"Version {item.version:03d} · {STATUS_LABELS.get(item.status, item.status)}").classes("font-bold")
                        ui.label(f"Rating: {item.rating}/5 · Seed: {item.seed}").classes("text-sm")
                        ui.label(f"Model: {item.checkpoint or '—'}").classes("text-xs text-gray-500")
                        ui.label(item.notes or "No director notes.").classes("text-sm")
            ui.button("Close", on_click=dialog.close).props("flat")
        dialog.open()

    async def generate_new_version(self, item: ImageAssetVersion) -> None:
        project = self.active_project
        if not project:
            return
        prompt = next(
            (p for p in load_latest_prompts(project)
             if p.scene_number == item.scene_number and p.shot_number == item.shot_number),
            None,
        )
        if prompt is None:
            ui.notify("No saved master prompt exists for this shot", type="warning")
            return
        job_id = job_queue.submit(
            f"New Version {item.asset_id}", ImageService.generate_shot, project, prompt,
            profile_id=item.profile_id, checkpoint=item.checkpoint or None,
            project_name=project,
        )
        self.status.set_text(f"Generating a new version for {item.asset_id}...")
        while True:
            job = job_queue.get(job_id)
            if job is None:
                ui.notify("Image job disappeared", type="negative")
                return
            if job.status is JobStatus.COMPLETED:
                ui.notify("New image version generated", type="positive")
                app_state.notify_content_changed()
                return
            if job.status is JobStatus.FAILED:
                ui.notify(job.error or "Image generation failed", type="negative", multi_line=True)
                return
            if job.status is JobStatus.CANCELLED:
                ui.notify("Image generation cancelled", type="warning")
                return
            await asyncio.sleep(0.75)
