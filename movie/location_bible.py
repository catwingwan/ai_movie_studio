"""Location Bible orchestration."""
from __future__ import annotations
from typing import Any
from movie.asset_manager import AssetManager
from movie.location_bible_schema import LocationBible
from movie.production_asset_ai import generate_location_bible
from movie.scene_storage import load_scenes


def load_location_bibles(project_name: str) -> list[LocationBible]:
    return [LocationBible.from_dict(item, str(item.get("name", ""))) for item in AssetManager.list(project_name, "locations")]


def _location_name(scene: dict[str, Any]) -> str:
    return str(scene.get("location") or scene.get("heading") or "").strip()


def generate_location_bibles(project_name: str) -> list[LocationBible]:
    scenes = [scene.to_dict() if hasattr(scene, "to_dict") else scene for scene in load_scenes(project_name)]
    if not scenes:
        raise ValueError("Generate scenes before creating the Location Bible.")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for scene in scenes:
        name = _location_name(scene)
        if name:
            grouped.setdefault(name.casefold(), []).append(scene)
    existing = {item.name.casefold(): item for item in load_location_bibles(project_name)}
    output: list[LocationBible] = []
    for key, related in grouped.items():
        bible = existing.get(key)
        if bible is None:
            bible = generate_location_bible(_location_name(related[0]), related)
            AssetManager.save(project_name, "locations", bible.to_dict())
        output.append(bible)
    if not output:
        raise ValueError("No usable scene locations were found.")
    return output


def save_location_bible(project_name: str, data: dict[str, Any]) -> LocationBible:
    bible = LocationBible.from_dict(data, str(data.get("name", "")))
    AssetManager.save(project_name, "locations", bible.to_dict())
    return bible
