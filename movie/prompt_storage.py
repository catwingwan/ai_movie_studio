"""Versioned prompt persistence for storyboard shots."""
from __future__ import annotations

import json
from pathlib import Path

from movie.production_manager import ProductionManager
from movie.prompt_schema import PromptRecord


def prompt_root(project_name: str) -> Path:
    root = ProductionManager.ensure_structure(project_name) / "prompts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def shot_prompt_folder(project_name: str, scene_number: int, shot_number: int) -> Path:
    folder = prompt_root(project_name) / f"scene_{scene_number:03d}" / f"shot_{shot_number:03d}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def next_version(project_name: str, scene_number: int, shot_number: int) -> int:
    folder = shot_prompt_folder(project_name, scene_number, shot_number)
    versions: list[int] = []
    for path in folder.glob("prompt_v*.json"):
        try:
            versions.append(int(path.stem.replace("prompt_v", "")))
        except ValueError:
            continue
    return max(versions, default=0) + 1


def save_prompt(project_name: str, record: PromptRecord) -> Path:
    folder = shot_prompt_folder(project_name, record.scene_number, record.shot_number)
    path = folder / f"prompt_v{record.version:03d}.json"
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)
    latest = folder / "latest.json"
    latest.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_latest_prompt(project_name: str, scene_number: int, shot_number: int) -> PromptRecord | None:
    path = shot_prompt_folder(project_name, scene_number, shot_number) / "latest.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return PromptRecord.from_dict(data)


def load_latest_prompts(project_name: str) -> list[PromptRecord]:
    root = prompt_root(project_name)
    records: list[PromptRecord] = []
    for path in sorted(root.glob("scene_*/shot_*/latest.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records.append(PromptRecord.from_dict(data))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
    return sorted(records, key=lambda item: (item.scene_number, item.shot_number))
