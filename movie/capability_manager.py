"""Central capability checks for local AI engines and built-in workflows."""
from __future__ import annotations

from dataclasses import dataclass, field

from movie.comfyui_manager import ComfyUIManager
from movie.workflow_library import WorkflowLibrary
from services.comfyui_service import ComfyUIService


@dataclass(slots=True)
class CapabilityReport:
    comfyui_online: bool
    message: str
    checkpoints: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    selected_workflow: str = ""
    selected_checkpoint: str = ""
    ready: bool = False


class CapabilityManager:
    @classmethod
    def inspect(cls) -> CapabilityReport:
        settings = ComfyUIManager.load_settings()
        health = ComfyUIService.check()
        workflows = [item.id for item in WorkflowLibrary.list()]
        if not health.online:
            return CapabilityReport(False, health.message, workflows=workflows,
                                    selected_workflow=settings.library_workflow_id,
                                    selected_checkpoint=settings.checkpoint_name)
        try:
            checkpoints = ComfyUIService.discover_models().get("checkpoints", [])
        except Exception as error:  # noqa: BLE001
            return CapabilityReport(True, f"ComfyUI online, but model discovery failed: {error}", workflows=workflows)
        selected = settings.checkpoint_name if settings.checkpoint_name in checkpoints else ""
        if not selected and checkpoints:
            selected = checkpoints[0]
            settings.checkpoint_name = selected
            ComfyUIManager.save_settings(settings)
        ready = bool(selected and settings.library_workflow_id)
        message = "Ready for image generation" if ready else "Install/select a checkpoint to continue"
        return CapabilityReport(True, message, checkpoints, workflows,
                                settings.library_workflow_id, selected, ready)
