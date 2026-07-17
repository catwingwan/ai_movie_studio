from functools import partial
from typing import Callable

from nicegui import ui

from services.project_service import ProjectService
from movie.state import app_state


class ProjectPanel:
    """Create, list, open, and delete movie projects."""

    def __init__(self) -> None:
        self.selected_project: str | None = app_state.active_project
        self.project: dict | None = None
        self._listeners: list[Callable[[str | None], None]] = []

        ui.label("📁 Projects").classes("text-xl font-bold")

        self.active_label = ui.label(
            "No project selected"
        ).classes("text-sm text-gray-500")

        with ui.card().classes("w-full shadow-none border"):

            self.title = ui.input(
                "Movie title"
            ).classes("w-full")

            self.genre = ui.select(
                [
                    "Drama",
                    "Comedy",
                    "Sci-Fi",
                    "Action",
                    "Thriller",
                    "Fantasy",
                    "Horror",
                ],
                value="Drama",
                label="Genre",
            ).classes("w-full")

            self.theme = ui.input(
                "Theme"
            ).classes("w-full")

            with ui.row().classes("w-full gap-2"):

                ui.button(
                    "New Project",
                    icon="add",
                    on_click=self.create,
                ).classes("flex-1")

                ui.button(
                    icon="refresh",
                    on_click=self.refresh,
                ).props("flat")

        ui.separator()

        self.project_container = ui.column().classes(
            "w-full gap-2"
        )

        self.refresh()

    def add_project_listener(
        self,
        callback: Callable[[str | None], None],
    ) -> None:
        """Register a callback for active-project changes."""

        self._listeners.append(callback)

    def _notify_listeners(self) -> None:
        for callback in self._listeners:
            callback(self.selected_project)

    def create(self) -> None:
        title = (self.title.value or "").strip()
        theme = (self.theme.value or "").strip()

        if not title:
            ui.notify(
                "Movie title is required",
                type="warning",
            )
            return

        project_name = ProjectService.create(
            title=title,
            genre=self.genre.value or "Drama",
            theme=theme,
        )

        self.title.value = ""
        self.genre.value = "Drama"
        self.theme.value = ""

        self.refresh()
        self.open(project_name)

        ui.notify(
            f"Project created: {project_name}",
            type="positive",
        )

    def open(self, name: str) -> None:
        project = ProjectService.load(name)

        if project is None:
            ui.notify(
                f"Unable to load project: {name}",
                type="negative",
            )
            return

        self.selected_project = name
        self.project = project

        self.active_label.set_text(
            f"Active: {project.get('title', name)}"
        )

        self.refresh()
        app_state.set_active_project(name)
        self._notify_listeners()

        ui.notify(
            f"Opened: {project.get('title', name)}",
            type="positive",
        )

    def remove(self, name: str) -> None:
        ProjectService.delete(name)

        if self.selected_project == name:
            self.selected_project = None
            self.project = None
            self.active_label.set_text(
                "No project selected"
            )
            app_state.set_active_project(None)
            self._notify_listeners()

        self.refresh()

        ui.notify(
            f"Deleted: {name}",
            type="warning",
        )

    def refresh(self) -> None:
        self.project_container.clear()

        projects = ProjectService.list()

        with self.project_container:

            if not projects:
                ui.label(
                    "No projects yet"
                ).classes("text-sm text-gray-500")
                return

            for name in projects:
                is_active = name == self.selected_project

                card_classes = (
                    "w-full border-2 border-blue-500"
                    if is_active
                    else "w-full border"
                )

                with ui.card().classes(
                    f"{card_classes} shadow-none p-2"
                ):

                    with ui.row().classes(
                        "w-full items-center justify-between"
                    ):

                        with ui.row().classes(
                            "items-center gap-2"
                        ):
                            ui.icon(
                                "folder_open"
                                if is_active
                                else "folder"
                            )

                            ui.label(name).classes(
                                "font-medium"
                            )

                        with ui.row().classes(
                            "items-center gap-1"
                        ):

                            ui.button(
                                icon="open_in_new",
                                on_click=partial(
                                    self.open,
                                    name,
                                ),
                            ).props(
                                "flat round dense"
                            )

                            ui.button(
                                icon="delete",
                                color="negative",
                                on_click=partial(
                                    self.remove,
                                    name,
                                ),
                            ).props(
                                "flat round dense"
                            )