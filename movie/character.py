"""Character JSON storage helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path("data/projects")


def get_character_file(project_name: str) -> Path:
    return PROJECT_ROOT / project_name / "characters.json"


def init_characters(project_name: str) -> Path:
    file = get_character_file(project_name)
    if not file.exists():
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("[]", encoding="utf-8")
    return file


def load_characters(project_name: str) -> list[dict[str, Any]]:
    file = init_characters(project_name)
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(f"Unable to read {file}: {error}") from error

    if not isinstance(data, list):
        raise ValueError(f"Invalid character file: {file}")
    return data


def save_characters(project_name: str, characters: list[dict[str, Any]]) -> Path:
    file = get_character_file(project_name)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        json.dumps(characters, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return file
