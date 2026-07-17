"""Small dependency-free Ollama server and model health checker."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class OllamaHealth:
    online: bool
    selected_model: str
    installed_models: tuple[str, ...]
    model_available: bool
    message: str


class OllamaHealthService:
    BASE_URL = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    SELECTED_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    @classmethod
    def check(cls, timeout: float = 3.0) -> OllamaHealth:
        request = Request(f"{cls.BASE_URL}/api/tags", headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310 - local configured endpoint
                payload = json.loads(response.read().decode("utf-8"))
        except (URLError, HTTPError, TimeoutError, json.JSONDecodeError) as error:
            return OllamaHealth(
                online=False,
                selected_model=cls.SELECTED_MODEL,
                installed_models=(),
                model_available=False,
                message=f"Ollama unavailable: {error}",
            )

        models = tuple(
            item.get("name", "")
            for item in payload.get("models", [])
            if item.get("name")
        )
        available = cls.SELECTED_MODEL in models
        message = (
            f"Ready · {cls.SELECTED_MODEL}"
            if available
            else f"Ollama online, but {cls.SELECTED_MODEL} is not installed"
        )
        return OllamaHealth(
            online=True,
            selected_model=cls.SELECTED_MODEL,
            installed_models=models,
            model_available=available,
            message=message,
        )
