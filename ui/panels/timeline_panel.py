"""Visual scene timeline."""
from __future__ import annotations

from nicegui import ui


class TimelinePanel:
    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.studio = project_panel.studio
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label("🕒 Production Timeline").classes("text-2xl font-bold")
                ui.label("Chronological runtime and asset coverage for every scene.").classes("text-sm text-gray-500")
            ui.button("Refresh", icon="refresh", on_click=self.refresh).props("outline")
        self.header = ui.column().classes("w-full")
        self.timeline = ui.column().classes("w-full gap-2")
        self.studio.events.subscribe("project.changed", lambda _: self.refresh())
        self.studio.events.subscribe("content.refreshed", lambda _: self.refresh())
        self.studio.events.subscribe("content.updated", lambda _: self.refresh())
        self.refresh()

    def _project(self) -> str | None:
        return self.studio.active_project or self.project_panel.selected_project

    @staticmethod
    def _time(seconds: int) -> str:
        minutes, remainder = divmod(max(0, seconds), 60)
        return f"{minutes:02d}:{remainder:02d}"

    def refresh(self) -> None:
        project = self._project()
        self.header.clear()
        self.timeline.clear()
        if not project:
            with self.timeline:
                ui.label("Select a project to view the timeline.").classes("text-gray-500")
            return
        items = self.studio.timeline.build(project)
        total = self.studio.timeline.total_duration(project)
        with self.header:
            ui.label(f"{len(items)} scenes · total runtime {self._time(total)}").classes("text-sm text-gray-500")
        with self.timeline:
            if not items:
                ui.label("Generate scenes to create the timeline.").classes("text-gray-500")
                return
            for item in items:
                width = max(8.0, (item["duration_seconds"] / total * 100) if total else 8.0)
                with ui.card().classes("w-full p-3 shadow-none border"):
                    with ui.row().classes("w-full items-center gap-3 no-wrap"):
                        ui.label(self._time(item["start_seconds"])).classes("w-14 text-xs text-gray-500")
                        with ui.column().classes("gap-1 min-w-0 flex-grow"):
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(f"S{item['scene_number']:03d} · {item['heading']}").classes("font-medium truncate")
                                ui.label(f"{item['duration_seconds']}s").classes("text-xs text-gray-500")
                            with ui.row().classes("w-full h-3 bg-slate-100 rounded overflow-hidden"):
                                ui.element("div").style(f"width:{width}%; min-width:0.5rem").classes("h-full bg-blue-500 rounded")
                            ui.label(
                                f"{item['shots']} shots · {item['approved_images']} approved images · "
                                f"{item['videos']} videos · {item['production_progress'] * 100:.0f}% production"
                            ).classes("text-xs text-gray-500")
                        ui.label(self._time(item["end_seconds"])).classes("w-14 text-xs text-gray-500 text-right")
