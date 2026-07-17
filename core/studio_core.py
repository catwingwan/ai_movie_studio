"""Composition root for AI Movie Studio."""
from __future__ import annotations

from dataclasses import dataclass

from core.adapters import AssetManagerAdapter, CapabilityManagerAdapter, ProductionManagerAdapter
from core.ai_manager import AIManager
from core.continuity_manager import ContinuityManager
from core.character_manager import CharacterManager
from core.relationship_manager import RelationshipManager
from core.event_bus import EventBus
from core.production_board import ProductionBoardManager
from core.service_registry import ServiceRegistry
from core.timeline_manager import TimelineManager
from movie.state import app_state


@dataclass(slots=True)
class StudioCore:
    events: EventBus
    services: ServiceRegistry
    assets: AssetManagerAdapter
    production: ProductionManagerAdapter
    capabilities: CapabilityManagerAdapter
    ai: AIManager
    timeline: TimelineManager
    production_board: ProductionBoardManager
    continuity: ContinuityManager
    characters: CharacterManager
    relationships: RelationshipManager

    @property
    def active_project(self) -> str | None:
        return app_state.active_project

    def set_active_project(self, project: str | None) -> None:
        app_state.set_active_project(project)

    def notify_content_changed(self, stage: str | None = None, **payload) -> None:
        project = self.active_project
        app_state.notify_content_changed()
        self.events.publish("content.updated", project=project, stage=stage, **payload)
        if stage:
            self.events.publish(f"{stage}.updated", project=project, **payload)

    def health(self, project: str | None = None) -> dict:
        selected = project or self.active_project
        if not selected:
            return {"project": None, "progress": 0.0, "status": {}, "missing_assets": []}
        return self.production.get_health(selected)


def create_studio_core() -> StudioCore:
    events = EventBus()
    services = ServiceRegistry()
    core = StudioCore(
        events=events,
        services=services,
        assets=AssetManagerAdapter(),
        production=ProductionManagerAdapter(),
        capabilities=CapabilityManagerAdapter(),
        ai=AIManager(),
        timeline=TimelineManager(),
        production_board=ProductionBoardManager(),
        continuity=ContinuityManager(),
        characters=CharacterManager(),
        relationships=RelationshipManager(),
    )
    for name in ("events", "assets", "production", "capabilities", "ai", "timeline", "production_board", "continuity", "characters", "relationships"):
        services.register(name, getattr(core, name))

    app_state.on_project_changed(lambda project: events.publish("project.changed", project=project))
    app_state.on_content_changed(lambda project: events.publish("content.refreshed", project=project))
    return core
