"""Talent Department workspace for character production and continuity."""
from __future__ import annotations

from nicegui import ui

from movie.state import app_state


class TalentDepartmentPanel:
    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel
        self.studio = project_panel.studio
        self.output = ui.column().classes("w-full gap-4")
        self._timeline_widgets: dict[tuple[str, int], tuple[object, object, object, object]] = {}
        app_state.on_project_changed(self.refresh)
        app_state.on_content_changed(self.refresh)
        self.refresh(app_state.active_project)

    @property
    def active_project(self) -> str | None:
        return app_state.active_project or getattr(self.project_panel, "selected_project", None)

    def refresh(self, project_name: str | None = None) -> None:
        project = project_name or self.active_project
        self.output.clear()
        self._timeline_widgets.clear()
        with self.output:
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-0"):
                    ui.label("🎭 Talent Department").classes("text-2xl font-bold")
                    ui.label("Characters, references, timelines, relationships, and continuity.").classes("text-sm text-gray-500")
                ui.button("Refresh", icon="refresh", on_click=lambda: self.refresh(project))
            if not project:
                ui.label("Select a project first.").classes("text-gray-500")
                return

            characters = self.studio.characters.list_characters(project)
            issues = self.studio.continuity.inspect(project)
            relationships = self.studio.relationships.build(project)
            with ui.row().classes("w-full gap-3 flex-wrap"):
                self._metric("Characters", len(characters), "groups")
                self._metric("References", sum(len(item.reference_images) for item in characters), "collections")
                self._metric("Scene appearances", sum(len(item.scene_numbers) for item in characters), "movie")
                self._metric("Warnings", sum(1 for item in issues if item.get("character")), "warning")

            if not characters:
                ui.label("No Character Bible profiles found yet.").classes("text-gray-500")
                return

            for character in characters:
                self._character_card(project, character, issues, relationships)

    @staticmethod
    def _metric(label: str, value: int, icon: str) -> None:
        with ui.card().classes("shadow-none border min-w-40"):
            with ui.row().classes("items-center gap-3"):
                ui.icon(icon).classes("text-2xl text-primary")
                with ui.column().classes("gap-0"):
                    ui.label(str(value)).classes("text-2xl font-bold")
                    ui.label(label).classes("text-xs text-gray-500")

    def _character_card(self, project, character, issues, relationships) -> None:
        character_issues = [item for item in issues if item.get("character") == character.name]
        with ui.card().classes("w-full shadow-none border rounded-xl"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("gap-0"):
                    ui.label(character.name).classes("text-xl font-bold")
                    ui.label(character.role or "Character").classes("text-sm text-gray-500")
                with ui.row().classes("items-center gap-2"):
                    ui.badge(f"{len(character.scene_numbers)} scenes").props("outline")
                    ui.badge(f"{len(character.reference_images)} refs").props("outline color=positive")
                    if character_issues:
                        ui.badge(f"{len(character_issues)} warnings").props("color=warning")

            with ui.expansion("Character workspace", icon="badge").classes("w-full"):
                with ui.tabs().classes("w-full") as tabs:
                    overview_tab = ui.tab("Overview")
                    timeline_tab = ui.tab("Timeline")
                    references_tab = ui.tab("References")
                    relations_tab = ui.tab("Relationships")
                    continuity_tab = ui.tab("Continuity")
                with ui.tab_panels(tabs, value=overview_tab).classes("w-full bg-transparent"):
                    with ui.tab_panel(overview_tab):
                        with ui.grid(columns=2).classes("w-full gap-3"):
                            for key, value in character.appearance.items():
                                if value:
                                    with ui.column().classes("gap-0"):
                                        ui.label(key.replace("_", " ").title()).classes("text-xs uppercase text-gray-400")
                                        ui.label(value)
                        if character.personality:
                            ui.label("Personality").classes("text-xs uppercase text-gray-400 mt-3")
                            ui.label(character.personality)
                        notes = ui.textarea("Director notes", value=character.director_notes).classes("w-full")
                        ui.button(
                            "Save Notes",
                            icon="save",
                            on_click=lambda c=character, n=notes: self._save(project, c, n),
                        )
                    with ui.tab_panel(timeline_tab):
                        if not character.scene_states:
                            ui.label("No scene appearances.").classes("text-gray-500")
                        for state in character.scene_states:
                            with ui.card().classes("w-full shadow-none border"):
                                ui.label(f"Scene {state.scene_number:03d}").classes("font-bold")
                                wardrobe = ui.input("Wardrobe", value=state.wardrobe).classes("w-full")
                                emotion = ui.input("Emotion", value=state.emotion).classes("w-full")
                                notes = ui.input("Scene notes", value=state.notes).classes("w-full")
                                intentional = ui.checkbox("Intentional change", value=state.intentional_change)
                                self._timeline_widgets[(character.name, state.scene_number)] = (wardrobe, emotion, notes, intentional)
                        ui.button(
                            "Save Timeline",
                            icon="save",
                            on_click=lambda c=character: self._save(project, c, None),
                        )
                    with ui.tab_panel(references_tab):
                        if not character.reference_images:
                            ui.label("No approved image references yet.").classes("text-gray-500")
                        for ref in character.reference_images:
                            ui.label(
                                f"Scene {ref['scene_number']:03d} · Shot {ref['shot_number']:03d} · v{ref['version']:03d} · Rating {ref['rating']}/5"
                            ).classes("text-sm")
                    with ui.tab_panel(relations_tab):
                        related = [edge for edge in relationships if edge["source"] == character.name or edge["target"] == character.name]
                        if not related:
                            ui.label("No relationships inferred yet.").classes("text-gray-500")
                        for edge in related:
                            ui.label(f"{edge['source']} — {edge['relation'].replace('_', ' ')} → {edge['target']} ({edge['weight']})")
                    with ui.tab_panel(continuity_tab):
                        if not character_issues:
                            ui.label("No continuity warnings.").classes("text-positive")
                        for issue in character_issues:
                            with ui.card().classes("w-full shadow-none border-l-4 border-amber-500"):
                                ui.label(f"Scene {issue['scene_number']:03d}").classes("font-bold")
                                ui.label(issue["message"]).classes("text-sm")

    def _save(self, project, character, notes_widget) -> None:
        director_notes = notes_widget.value if notes_widget is not None else character.director_notes
        states = []
        for state in character.scene_states:
            widgets = self._timeline_widgets.get((character.name, state.scene_number))
            if widgets:
                wardrobe, emotion, notes, intentional = widgets
                states.append({
                    "scene_number": state.scene_number,
                    "wardrobe": wardrobe.value,
                    "emotion": emotion.value,
                    "notes": notes.value,
                    "intentional_change": intentional.value,
                })
            else:
                states.append({
                    "scene_number": state.scene_number,
                    "wardrobe": state.wardrobe,
                    "emotion": state.emotion,
                    "notes": state.notes,
                    "intentional_change": state.intentional_change,
                })
        self.studio.characters.save_character(
            project, character.name, director_notes=str(director_notes or ""), scene_states=states
        )
        self.studio.events.publish("character.updated", project=project, character=character.name)
        app_state.notify_content_changed()
        ui.notify(f"{character.name} updated", type="positive")
