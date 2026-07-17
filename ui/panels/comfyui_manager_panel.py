"""Simple ComfyUI engine and built-in workflow configuration workspace."""
from __future__ import annotations

from nicegui import run, ui

from services.comfyui_manager_service import ComfyUIManagerService


class ComfyUIManagerPanel:
    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.settings = ComfyUIManagerService.load_settings()

        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("🧩 ComfyUI Engine").classes("text-2xl font-bold")
                ui.label(
                    "AI Movie Studio owns the workflow. Choose an installed model—no node mapping required."
                ).classes("text-sm text-gray-500")
            ui.button("Refresh Capabilities", icon="refresh", on_click=self.refresh).props("outline")

        self.health_label = ui.label("Checking ComfyUI...").classes("text-sm text-gray-500")

        with ui.card().classes("w-full shadow-none border rounded-xl"):
            ui.label("Connection").classes("text-lg font-bold")
            with ui.row().classes("w-full items-end gap-3"):
                self.base_url = ui.input("ComfyUI URL", value=self.settings.base_url).classes("flex-grow")
                ui.button("Save & Check", icon="health_and_safety", on_click=self.save_and_check)

        with ui.card().classes("w-full shadow-none border rounded-xl"):
            ui.label("Image Engine").classes("text-lg font-bold")
            ui.label(
                "The built-in Standard Checkpoint workflow supports SD 1.5, SDXL, and compatible single-checkpoint models."
            ).classes("text-xs text-gray-500")
            with ui.row().classes("w-full items-end gap-3"):
                workflows = {
                    item.id: item.name for item in ComfyUIManagerService.list_library_workflows()
                }
                self.workflow_select = ui.select(
                    workflows,
                    value=self.settings.library_workflow_id or "standard_checkpoint",
                    label="Built-in Workflow",
                ).classes("w-72")
                initial_checkpoint = self.settings.checkpoint_name or None
                initial_options = (
                    {initial_checkpoint: initial_checkpoint}
                    if initial_checkpoint
                    else {}
                )
                self.checkpoint_select = ui.select(
                    initial_options,
                    value=initial_checkpoint,
                    label="Installed Checkpoint",
                ).classes("flex-grow")
                ui.button("Use Selection", icon="check", on_click=self.save_selection)
            self.ready_label = ui.label("Discovering installed checkpoints...").classes("text-sm text-gray-500")

        with ui.expansion("Developer Mode: custom API workflows", icon="code").classes("w-full"):
            ui.label(
                "Optional only. Built-in generation does not need workflow files or node IDs."
            ).classes("text-sm text-gray-500")
            self.upload = ui.upload(
                label="Import custom API workflow",
                auto_upload=True,
                on_upload=self.import_custom,
            ).props("accept=.json").classes("w-full")
            self.custom_label = ui.label(
                f"Active custom workflow: {self.settings.workflow_name or 'None'}"
            ).classes("text-xs text-gray-500")

        ui.timer(0.1, self.refresh, once=True)

    async def save_and_check(self) -> None:
        self.settings.base_url = str(self.base_url.value or "http://127.0.0.1:8188").rstrip("/")
        ComfyUIManagerService.save_settings(self.settings)
        await self.refresh()

    async def refresh(self) -> None:
        self.health_label.set_text("Checking ComfyUI and installed models...")
        report = await run.io_bound(ComfyUIManagerService.inspect_capabilities)
        self.settings = ComfyUIManagerService.load_settings()
        self.health_label.set_text(report.message if report.comfyui_online else report.message)
        self.health_label.classes(
            replace="text-sm text-green-700" if report.comfyui_online else "text-sm text-red-600"
        )
        checkpoint_options = {item: item for item in report.checkpoints}
        selected = report.selected_checkpoint or (report.checkpoints[0] if report.checkpoints else None)
        if selected and selected not in checkpoint_options:
            checkpoint_options[selected] = selected
        self.checkpoint_select.set_options(
            checkpoint_options,
            value=selected,
        )
        if report.ready:
            self.ready_label.set_text(f"✓ Ready · {selected}")
            self.ready_label.classes(replace="text-sm text-green-700")
        elif report.comfyui_online and not report.checkpoints:
            self.ready_label.set_text("⚠ ComfyUI is online, but no checkpoints were detected.")
            self.ready_label.classes(replace="text-sm text-amber-700")
        else:
            self.ready_label.set_text("Connect ComfyUI and select an installed checkpoint.")
            self.ready_label.classes(replace="text-sm text-gray-500")

    async def save_selection(self) -> None:
        workflow_id = str(self.workflow_select.value or "standard_checkpoint")
        checkpoint = str(self.checkpoint_select.value or "")
        if not checkpoint:
            ui.notify("No installed checkpoint is available", type="warning")
            return
        self.settings.library_workflow_id = workflow_id
        self.settings.checkpoint_name = checkpoint
        ComfyUIManagerService.save_settings(self.settings)
        ui.notify("Image engine is ready", type="positive")
        await self.refresh()

    async def import_custom(self, event) -> None:
        try:
            content = await event.file.read()
            name = ComfyUIManagerService.import_workflow_bytes(event.file.name, content)
            self.settings = ComfyUIManagerService.load_settings()
            self.custom_label.set_text(f"Active custom workflow: {name}")
            ui.notify("Custom workflow imported for Developer Mode", type="positive")
        except Exception as error:  # noqa: BLE001
            ui.notify(str(error), type="negative", multi_line=True)
