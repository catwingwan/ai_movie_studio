"""Production asset manager UI for character, location, prop, and wardrobe bibles."""

from __future__ import annotations

from functools import partial

from nicegui import ui

from movie.state import app_state
from services.production_service import AssetService, ProductionService


class AssetsPanel:
    ASSET_TYPES = {
        "characters": "Character Bible",
        "locations": "Location Bible",
        "props": "Prop Library",
        "wardrobe": "Wardrobe",
    }

    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.asset_type = "characters"

        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("📦 Production Assets").classes("text-2xl font-bold")
                ui.label(
                    "Reusable character, location, prop, and wardrobe references."
                ).classes("text-sm text-gray-500")
            ui.button(icon="refresh", on_click=self.refresh).props("flat round")

        self.summary = ui.row().classes("w-full gap-3")

        self.type_select = ui.select(
            self.ASSET_TYPES,
            value=self.asset_type,
            label="Asset library",
            on_change=self._change_type,
        ).classes("w-full max-w-sm")

        with ui.card().classes("w-full shadow-none border"):
            ui.label("Add production asset").classes("font-bold")
            self.name = ui.input("Name").classes("w-full")
            self.description = ui.textarea("Visual description").classes("w-full")
            self.tags = ui.input("Tags (comma separated)").classes("w-full")
            self.prompt = ui.textarea("Consistency prompt").classes("w-full")
            self.negative_prompt = ui.textarea("Negative prompt").classes("w-full")
            ui.button("Save Asset", icon="save", on_click=self.save_asset)

        self.status = ui.label("Select a project to manage assets.").classes(
            "text-sm text-gray-500"
        )
        self.container = ui.column().classes("w-full gap-3")

        app_state.on_project_changed(self._on_change)
        app_state.on_content_changed(self._on_change)
        self.refresh()

    def _project_name(self) -> str | None:
        return app_state.active_project or self.project_panel.selected_project

    def _on_change(self, _project_name: str | None) -> None:
        self.refresh()

    def _change_type(self, event) -> None:
        self.asset_type = event.value
        self.refresh()

    def save_asset(self) -> None:
        project = self._project_name()
        if not project:
            ui.notify("Select a project first", type="warning")
            return
        name = (self.name.value or "").strip()
        if not name:
            ui.notify("Asset name is required", type="warning")
            return
        data = {
            "name": name,
            "description": (self.description.value or "").strip(),
            "tags": [item.strip() for item in (self.tags.value or "").split(",") if item.strip()],
            "prompt": (self.prompt.value or "").strip(),
            "negative_prompt": (self.negative_prompt.value or "").strip(),
            "status": "draft",
        }
        AssetService.save(project, self.asset_type, data)
        self.name.value = ""
        self.description.value = ""
        self.tags.value = ""
        self.prompt.value = ""
        self.negative_prompt.value = ""
        app_state.notify_content_changed()
        ui.notify("Asset saved", type="positive")

    def delete_asset(self, asset_id: str) -> None:
        project = self._project_name()
        if not project:
            return
        AssetService.delete(project, self.asset_type, asset_id)
        app_state.notify_content_changed()
        ui.notify("Asset deleted", type="warning")

    @staticmethod
    def _format_bytes(value: int) -> str:
        amount = float(value)
        for unit in ("B", "KB", "MB", "GB"):
            if amount < 1024 or unit == "GB":
                return f"{amount:.1f} {unit}"
            amount /= 1024
        return f"{amount:.1f} GB"

    def refresh(self) -> None:
        self.container.clear()
        self.summary.clear()
        project = self._project_name()
        if not project:
            self.status.set_text("Select a project to manage assets.")
            return

        ProductionService.ensure_structure(project)
        stats = ProductionService.statistics(project)
        self.status.set_text(f"Active project: {project}")

        with self.summary:
            for label, value in (
                ("Characters", stats.character_assets),
                ("Locations", stats.location_assets),
                ("Props", stats.prop_assets),
                ("Shots", stats.shots),
                ("Disk", self._format_bytes(stats.disk_bytes)),
            ):
                with ui.card().classes("shadow-none border min-w-28 p-3"):
                    ui.label(str(value)).classes("text-xl font-bold")
                    ui.label(label).classes("text-xs text-gray-500")

        assets = AssetService.list(project, self.asset_type)
        with self.container:
            if not assets:
                ui.label(f"No {self.ASSET_TYPES[self.asset_type].lower()} assets yet.").classes(
                    "text-sm text-gray-500"
                )
                return
            for asset in assets:
                with ui.card().classes("w-full shadow-none border"):
                    with ui.row().classes("w-full items-start justify-between"):
                        with ui.column().classes("gap-1"):
                            ui.label(asset.get("name", asset.get("id", "Asset"))).classes(
                                "text-lg font-bold"
                            )
                            description = str(asset.get("description", "")).strip()
                            if description:
                                ui.label(description).classes("text-sm text-gray-600")
                            tags = asset.get("tags", [])
                            if isinstance(tags, list) and tags:
                                with ui.row().classes("gap-1"):
                                    for tag in tags:
                                        ui.badge(str(tag)).props("outline")
                            prompt = str(asset.get("prompt", "")).strip()
                            if prompt:
                                ui.label("Consistency prompt").classes(
                                    "text-xs uppercase tracking-wide text-gray-400 mt-2"
                                )
                                ui.label(prompt).classes("text-sm")
                        ui.button(
                            icon="delete",
                            color="negative",
                            on_click=partial(self.delete_asset, str(asset.get("id", ""))),
                        ).props("flat round")
