"""Reusable NiceGUI foundation for project content workspaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

import asyncio

from nicegui import ui

from movie.state import app_state
from services.job_queue import JobStatus, job_queue

ContentT = TypeVar("ContentT")


class BaseContentPanel(ABC, Generic[ContentT]):
    """Common loading, generation, refresh, and error handling for panels."""

    title = "Content"
    title_icon = "description"
    generate_label = "Generate"
    generate_icon = "auto_awesome"
    select_message = "Select a project first."
    missing_message = "No content generated yet."
    generating_message = "Generating content..."
    success_notification = "Content generated"

    def __init__(self, project_panel) -> None:
        self.project_panel = project_panel

        with ui.row().classes("w-full items-center justify-between"):
            ui.label(f"{self.title_icon} {self.title}").classes("text-2xl font-bold")
            self.generate_button = ui.button(
                self.generate_label,
                icon=self.generate_icon,
                on_click=self.generate,
            )

        self.status = ui.label(self.select_message).classes("text-sm text-gray-500")
        self.output = ui.column().classes("w-full gap-3")

        app_state.on_project_changed(self.refresh)
        app_state.on_content_changed(self.refresh)
        self.refresh(app_state.active_project)

    @property
    def active_project(self) -> str | None:
        """Return the shared project, with legacy ProjectPanel fallback."""
        return app_state.active_project or getattr(
            self.project_panel,
            "selected_project",
            None,
        )

    def refresh(self, project_name: str | None = None) -> None:
        """Load and render persisted content for the current project."""
        project = project_name or self.active_project
        self.output.clear()

        if not project:
            self.status.set_text(self.select_message)
            return

        try:
            content = self.load_content(project)
        except Exception as error:
            self.status.set_text(f"Unable to load {self.title.lower()}.")
            ui.notify(
                str(error),
                type="negative",
                multi_line=True,
            )
            return

        if not self.has_content(content):
            self.status.set_text(self.missing_message)
            return

        self.render_content(content)
        self.status.set_text(self.loaded_message(content))

    async def generate(self) -> None:
        """Generate, validate, persist, and render panel content."""
        project = self.active_project
        if not project:
            ui.notify(self.select_message, type="warning")
            return

        self.generate_button.disable()
        self.status.set_text(self.generating_message)

        try:
            job_id = job_queue.submit(
                self.generate_label,
                self.generate_content,
                project,
                project_name=project,
            )
            self.status.set_text(f"{self.generate_label} queued...")

            while True:
                job = job_queue.get(job_id)
                if job is None:
                    raise RuntimeError("AI job disappeared from the queue.")
                if job.status is JobStatus.COMPLETED:
                    content = job.result
                    break
                if job.status is JobStatus.FAILED:
                    raise RuntimeError(job.error or "AI job failed.")
                if job.status is JobStatus.CANCELLED:
                    raise RuntimeError("AI job was cancelled.")
                self.status.set_text(
                    f"{self.generate_label}: {job.message.lower()}..."
                )
                await asyncio.sleep(0.5)

            if not self.has_content(content):
                raise RuntimeError(
                    f"The AI returned no usable {self.title.lower()} content."
                )

            # The background AI task has completed successfully at this point.
            # Keep UI refresh errors separate so they cannot misreport the AI job.
            try:
                self.render_content(content)
            except Exception as render_error:
                self.status.set_text(
                    f"{self.title} generated, but the preview could not be rendered."
                )
                ui.notify(
                    f"Generation completed. Preview error: {render_error}",
                    type="warning",
                    multi_line=True,
                )
            else:
                self.status.set_text(self.generated_message(content))
                ui.notify(self.success_notification, type="positive")

            app_state.notify_content_changed()
        except Exception as error:
            self.status.set_text(f"{self.title} generation failed.")
            ui.notify(
                str(error),
                type="negative",
                multi_line=True,
            )
        finally:
            self.generate_button.enable()

    def has_content(self, content: ContentT) -> bool:
        """Return whether loaded/generated content is useful."""
        if isinstance(content, str):
            return bool(content.strip())
        return bool(content)

    def loaded_message(self, content: ContentT) -> str:
        return f"Existing {self.title.lower()} loaded."

    def generated_message(self, content: ContentT) -> str:
        return f"{self.title} generated successfully."

    @abstractmethod
    def load_content(self, project_name: str) -> ContentT:
        """Load persisted content for a project."""

    @abstractmethod
    def generate_content(self, project_name: str) -> ContentT:
        """Generate and persist content for a project."""

    @abstractmethod
    def render_content(self, content: ContentT) -> None:
        """Render content inside ``self.output``."""
