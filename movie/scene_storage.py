"""Atomic persistence helpers for structured scene files."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from movie.scene_schema import Scene
from movie.storage import project_path


def scene_folder(project_name: str) -> Path:
    return project_path(project_name) / "scenes"


def load_scenes(project_name: str) -> list[Scene]:
    folder = scene_folder(project_name)
    if not folder.exists():
        return []

    scenes: list[Scene] = []
    for index, file in enumerate(sorted(folder.glob("scene_*.json")), start=1):
        data = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Invalid scene file: {file.name}")
        scenes.append(Scene.from_dict(data, index))

    return sorted(scenes, key=lambda item: item.scene_number)


def save_scene(project_name: str, scene: Scene) -> Path:
    folder = scene_folder(project_name)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"scene_{scene.scene_number:03d}.json"
    path.write_text(
        json.dumps(scene.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def replace_scenes(project_name: str, scenes: list[Scene]) -> Path:
    """Replace the scene directory only after every new file is written."""
    project_dir = project_path(project_name)
    project_dir.mkdir(parents=True, exist_ok=True)
    target = scene_folder(project_name)

    temp_dir = Path(tempfile.mkdtemp(prefix="scenes_", dir=project_dir))
    try:
        for scene in scenes:
            path = temp_dir / f"scene_{scene.scene_number:03d}.json"
            path.write_text(
                json.dumps(scene.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        backup = project_dir / "scenes_backup"
        if backup.exists():
            shutil.rmtree(backup)
        if target.exists():
            target.rename(backup)
        temp_dir.rename(target)
        if backup.exists():
            shutil.rmtree(backup)
        return target
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise
