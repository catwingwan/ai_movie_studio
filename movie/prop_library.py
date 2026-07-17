"""Prop Library orchestration."""
from __future__ import annotations
from typing import Any
from movie.asset_manager import AssetManager
from movie.production_asset_ai import generate_props_for_scene
from movie.prop_schema import PropAsset
from movie.scene_storage import load_scenes


def load_props(project_name: str) -> list[PropAsset]:
    return [PropAsset.from_dict(item, str(item.get("name", ""))) for item in AssetManager.list(project_name, "props")]


def generate_props(project_name: str) -> list[PropAsset]:
    scenes = [scene.to_dict() if hasattr(scene, "to_dict") else scene for scene in load_scenes(project_name)]
    if not scenes:
        raise ValueError("Generate scenes before creating the Prop Library.")
    merged = {item.name.casefold(): item for item in load_props(project_name)}
    for scene in scenes:
        for prop in generate_props_for_scene(scene):
            key = prop.name.casefold()
            current = merged.get(key)
            if current is not None:
                current.scenes = sorted(set(current.scenes + prop.scenes))
                AssetManager.save(project_name, "props", current.to_dict())
            else:
                merged[key] = prop
                AssetManager.save(project_name, "props", prop.to_dict())
    return sorted(merged.values(), key=lambda item: item.name.casefold())


def save_prop(project_name: str, data: dict[str, Any]) -> PropAsset:
    prop = PropAsset.from_dict(data, str(data.get("name", "")))
    AssetManager.save(project_name, "props", prop.to_dict())
    return prop
