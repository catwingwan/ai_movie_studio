"""Persistence helpers for scene-by-scene storyboard shot files."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from movie.scene_storage import load_scenes
from movie.storage import project_path
from movie.storyboard_schema import SceneStoryboard, StoryboardShot


def storyboard_root(project_name: str) -> Path:
    return project_path(project_name) / "storyboard"


def scene_storyboard_folder(project_name: str, scene_number: int) -> Path:
    return storyboard_root(project_name) / f"scene_{scene_number:03d}"


def load_scene_shots(project_name: str, scene_number: int) -> list[StoryboardShot]:
    folder = scene_storyboard_folder(project_name, scene_number)
    if not folder.exists():
        return []

    shots: list[StoryboardShot] = []
    for index, file in enumerate(sorted(folder.glob("shot_*.json")), start=1):
        data = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"Invalid storyboard file: {file.name}")
        shots.append(StoryboardShot.from_dict(data, scene_number, index))

    return sorted(shots, key=lambda item: item.shot_number)


def load_storyboards(project_name: str) -> list[SceneStoryboard]:
    scenes = load_scenes(project_name)
    storyboards: list[SceneStoryboard] = []
    for scene in scenes:
        shots = load_scene_shots(project_name, scene.scene_number)
        if shots:
            storyboards.append(
                SceneStoryboard(
                    scene_number=scene.scene_number,
                    scene_heading=scene.heading,
                    shots=shots,
                )
            )
    return storyboards


def save_shot(project_name: str, shot: StoryboardShot) -> Path:
    folder = scene_storyboard_folder(project_name, shot.scene_number)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"shot_{shot.shot_number:03d}.json"
    path.write_text(
        json.dumps(shot.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def replace_scene_shots(
    project_name: str,
    scene_number: int,
    shots: list[StoryboardShot],
) -> Path:
    """Atomically replace one scene's storyboard after all shots validate."""
    root = storyboard_root(project_name)
    root.mkdir(parents=True, exist_ok=True)
    target = scene_storyboard_folder(project_name, scene_number)
    temp_dir = Path(tempfile.mkdtemp(prefix=f"scene_{scene_number:03d}_", dir=root))

    try:
        for shot in shots:
            path = temp_dir / f"shot_{shot.shot_number:03d}.json"
            path.write_text(
                json.dumps(shot.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        backup = root / f"scene_{scene_number:03d}_backup"
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
