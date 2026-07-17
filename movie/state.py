"""Shared application state for the currently active movie project."""

from __future__ import annotations

import logging
from collections.abc import Callable

ProjectListener = Callable[[str | None], None]
logger = logging.getLogger(__name__)


class AppState:
    """Small observable state container shared by all NiceGUI panels.

    Listener failures are isolated so one broken panel cannot make a completed
    generation job appear to have failed in another panel.
    """

    def __init__(self) -> None:
        self._active_project: str | None = None
        self._project_listeners: list[ProjectListener] = []
        self._content_listeners: list[ProjectListener] = []

    @property
    def active_project(self) -> str | None:
        return self._active_project

    def set_active_project(self, project_name: str | None) -> None:
        changed = project_name != self._active_project
        self._active_project = project_name

        if changed:
            self._emit(self._project_listeners, project_name)

        self._emit(self._content_listeners, project_name)

    def on_project_changed(self, callback: ProjectListener) -> None:
        if callback not in self._project_listeners:
            self._project_listeners.append(callback)

    def on_content_changed(self, callback: ProjectListener) -> None:
        if callback not in self._content_listeners:
            self._content_listeners.append(callback)

    def notify_content_changed(self) -> None:
        self._emit(self._content_listeners, self._active_project)

    @staticmethod
    def _emit(listeners: list[ProjectListener], project_name: str | None) -> None:
        for callback in tuple(listeners):
            try:
                callback(project_name)
            except Exception:  # noqa: BLE001 - UI listeners must be isolated
                logger.exception(
                    "AppState listener failed | callback=%r | project=%r",
                    callback,
                    project_name,
                )


app_state = AppState()


def set_active(project_name: str | None) -> None:
    app_state.set_active_project(project_name)


def get_active() -> str | None:
    return app_state.active_project
