"""Project content persistence helpers."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path("data/projects")


def project_path(project_name: str) -> Path:
    return PROJECT_ROOT / project_name


def read_text_file(project_name: str, filename: str) -> str:
    file = project_path(project_name) / filename
    if not file.exists():
        return ""
    return file.read_text(encoding="utf-8")


def write_text_file(project_name: str, filename: str, content: str) -> Path:
    folder = project_path(project_name)
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / filename
    file.write_text(content, encoding="utf-8")
    return file


def read_story(project_name: str) -> str:
    return read_text_file(project_name, "story.md")


def read_screenplay(project_name: str) -> str:
    return read_text_file(project_name, "screenplay.md")


def write_screenplay(project_name: str, screenplay: str) -> Path:
    return write_text_file(project_name, "screenplay.md", screenplay)


def save_scene(project_name: str, scene) -> None:
    from movie.scene_storage import save_scene as _save_scene
    _save_scene(project_name, scene)


def load_scenes(project_name: str):
    from movie.scene_storage import load_scenes as _load_scenes
    return _load_scenes(project_name)
