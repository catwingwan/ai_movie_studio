"""Thread-safe, failure-isolated application event bus."""
from __future__ import annotations

import asyncio
import inspect
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Callable

logger = logging.getLogger(__name__)
EventHandler = Callable[["StudioEvent"], Any]


@dataclass(frozen=True, slots=True)
class StudioEvent:
    name: str
    project: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EventBus:
    """Publish/subscribe bus supporting exact and wildcard subscriptions."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(self, event_name: str, handler: EventHandler) -> Callable[[], None]:
        with self._lock:
            if handler not in self._handlers[event_name]:
                self._handlers[event_name].append(handler)
        return lambda: self.unsubscribe(event_name, handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        with self._lock:
            handlers = self._handlers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, event_name: str, *, project: str | None = None, **payload: Any) -> StudioEvent:
        event = StudioEvent(event_name, project, payload)
        with self._lock:
            handlers = tuple(self._handlers.get(event_name, ())) + tuple(self._handlers.get("*", ()))
        for handler in handlers:
            try:
                result = handler(event)
                if inspect.isawaitable(result):
                    self._schedule(result)
            except Exception:  # noqa: BLE001
                logger.exception("Studio event handler failed | event=%s | handler=%r", event_name, handler)
        return event

    @staticmethod
    def _schedule(awaitable: Any) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(awaitable)
        else:
            loop.create_task(awaitable)
