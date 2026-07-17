"""Application-facing ComfyUI Manager facade."""
from __future__ import annotations

from movie.comfyui_manager import ComfyUIManager, ComfyUISettings
from services.comfyui_service import ComfyUIService
from movie.capability_manager import CapabilityManager
from movie.workflow_library import WorkflowLibrary


class ComfyUIManagerService:
    load_settings = staticmethod(ComfyUIManager.load_settings)
    save_settings = staticmethod(ComfyUIManager.save_settings)
    list_workflows = staticmethod(ComfyUIManager.list_workflows)
    import_workflow_bytes = staticmethod(ComfyUIManager.import_workflow_bytes)
    delete_workflow = staticmethod(ComfyUIManager.delete_workflow)
    inspect_workflow = staticmethod(ComfyUIManager.inspect_workflow)
    auto_map = staticmethod(ComfyUIManager.auto_map)
    activate_workflow = staticmethod(ComfyUIManager.activate_workflow)
    desktop_workflow_candidates = staticmethod(ComfyUIManager.desktop_workflow_candidates)
    scan_desktop_workflows = staticmethod(ComfyUIManager.scan_desktop_workflows)
    check_health = staticmethod(ComfyUIService.check)
    discover_models = staticmethod(ComfyUIService.discover_models)
    queue_prompt = staticmethod(ComfyUIService.queue_prompt)
    inspect_capabilities = staticmethod(CapabilityManager.inspect)
    list_library_workflows = staticmethod(WorkflowLibrary.list)


__all__ = ["ComfyUIManagerService", "ComfyUISettings"]
