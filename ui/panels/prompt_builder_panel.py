"""Master prompt composition, preview, validation, and versioning UI."""
from __future__ import annotations

from functools import partial

from nicegui import ui

from movie.prompt_schema import PromptRecord
from movie.prompt_storage import next_version, save_prompt
from movie.prompt_validator import validate_prompt
from movie.state import app_state
from services.prompt_service import PromptService
from ui.panels.base_content_panel import BaseContentPanel


class PromptBuilderPanel(BaseContentPanel[list[PromptRecord]]):
    title = "Prompt Builder"
    title_icon = "🧠"
    generate_label = "Build Master Prompts"
    generate_icon = "auto_fix_high"
    missing_message = "No prompts yet. Generate Storyboard, Character Bible, and Location Bible first."
    generating_message = "Combining production assets into versioned image prompts..."
    success_notification = "Master prompts built"

    def __init__(self, project_panel) -> None:
        styles = PromptService.styles()
        self._style_options = {style.id: style.name for style in styles}
        self._selected_style = styles[0].id
        with ui.card().classes("w-full shadow-none border rounded-xl mb-3"):
            with ui.row().classes("w-full items-center gap-4"):
                self.style_select = ui.select(
                    self._style_options,
                    value=self._selected_style,
                    label="Visual Style",
                    on_change=self._style_changed,
                ).classes("w-72")
                self.style_description = ui.label(styles[0].description).classes("text-sm text-gray-500 flex-grow")
        super().__init__(project_panel)

    def _style_changed(self, event) -> None:
        self._selected_style = str(event.value)
        style = next(item for item in PromptService.styles() if item.id == self._selected_style)
        self.style_description.set_text(style.description)

    def refresh(self, project_name: str | None = None) -> None:
        project = project_name or getattr(self, "active_project", None)
        if project:
            self._selected_style = PromptService.project_style(project)
            if hasattr(self, "style_select"):
                self.style_select.value = self._selected_style
                style = next(item for item in PromptService.styles() if item.id == self._selected_style)
                self.style_description.set_text(style.description)
        super().refresh(project_name)

    def load_content(self, project_name: str) -> list[PromptRecord]:
        return PromptService.load(project_name)

    def generate_content(self, project_name: str) -> list[PromptRecord]:
        return PromptService.generate(project_name, self._selected_style)

    def loaded_message(self, content: list[PromptRecord]) -> str:
        return f"{len(content)} latest shot prompts loaded."

    def generated_message(self, content: list[PromptRecord]) -> str:
        return f"{len(content)} shot prompts ready for Image Studio."

    def _save_revision(self, record: PromptRecord, prompt_area, negative_area) -> None:
        project = self.active_project
        if not project:
            return
        revised = PromptRecord.from_dict(record.to_dict())
        revised.prompt = str(prompt_area.value or "").strip()
        revised.negative_prompt = str(negative_area.value or "").strip()
        revised.version = next_version(project, record.scene_number, record.shot_number)
        revised.quality_score, revised.warnings = validate_prompt(revised)
        save_prompt(project, revised)
        app_state.notify_content_changed()
        ui.notify(f"Prompt v{revised.version:03d} saved", type="positive")

    @staticmethod
    def _copy(text: str) -> None:
        ui.run_javascript(f"navigator.clipboard.writeText({text!r})")
        ui.notify("Prompt copied", type="positive")

    def render_content(self, content: list[PromptRecord]) -> None:
        self.output.clear()
        ready = sum(1 for item in content if item.quality_score >= 75)
        with self.output:
            with ui.row().classes("w-full gap-3"):
                ui.badge(f"{len(content)} prompts").props("outline color=primary")
                ui.badge(f"{ready} production-ready").props("outline color=positive")
                ui.badge(f"Style: {self._style_options.get(self._selected_style, self._selected_style)}").props("outline")

            for record in content:
                score_color = "positive" if record.quality_score >= 75 else "warning"
                with ui.card().classes("w-full shadow-none border rounded-xl"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.column().classes("gap-0"):
                            ui.label(
                                f"Scene {record.scene_number:03d} · Shot {record.shot_number:03d}"
                            ).classes("text-lg font-bold")
                            details = [
                                record.location_name,
                                ", ".join(record.character_names),
                                ", ".join(record.prop_names),
                            ]
                            ui.label(" · ".join(item for item in details if item)).classes("text-sm text-gray-500")
                        with ui.row().classes("items-center gap-2"):
                            ui.badge(f"Quality {record.quality_score}%").props(f"outline color={score_color}")
                            ui.badge(f"v{record.version:03d}").props("outline")

                    prompt_area = ui.textarea("Master prompt", value=record.prompt).classes("w-full").props("autogrow")
                    negative_area = ui.textarea(
                        "Negative prompt", value=record.negative_prompt
                    ).classes("w-full").props("autogrow")

                    if record.warnings:
                        with ui.expansion("Prompt checks", icon="fact_check").classes("w-full"):
                            for warning in record.warnings:
                                ui.label(f"⚠ {warning}").classes("text-sm text-amber-700")
                    else:
                        ui.label("✓ Prompt passed all production checks").classes("text-sm text-green-700")

                    with ui.row().classes("gap-2"):
                        ui.button(
                            "Save Revision",
                            icon="save",
                            on_click=partial(self._save_revision, record, prompt_area, negative_area),
                        )
                        ui.button(
                            "Copy Prompt",
                            icon="content_copy",
                            on_click=partial(self._copy, record.prompt),
                        ).props("outline")
