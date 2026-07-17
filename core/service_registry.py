"""Dependency registry used by Studio Core and UI panels."""
from __future__ import annotations

from typing import Any, TypeVar

T = TypeVar("T")


class ServiceRegistry:
    def __init__(self) -> None:
        self._services: dict[str, Any] = {}

    def register(self, name: str, service: Any, *, replace: bool = False) -> None:
        if not replace and name in self._services:
            raise KeyError(f"Service already registered: {name}")
        self._services[name] = service

    def get(self, name: str, expected_type: type[T] | None = None) -> T | Any:
        if name not in self._services:
            raise KeyError(f"Unknown service: {name}")
        service = self._services[name]
        if expected_type is not None and not isinstance(service, expected_type):
            raise TypeError(f"Service {name!r} is not {expected_type.__name__}")
        return service

    def has(self, name: str) -> bool:
        return name in self._services

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._services))
