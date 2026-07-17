"""Reusable JSON asset storage for production bibles and reference libraries."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from movie.production_manager import ProductionManager

ASSET_TYPES = {"characters", "locations", "props", "wardrobe", "references"}


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip()).strip("_").lower()
    return cleaned or "asset"


class AssetManager:
    @staticmethod
    def _folder(project_name: str, asset_type: str) -> Path:
        if asset_type not in ASSET_TYPES:
            raise ValueError(f"Unsupported asset type: {asset_type}")
        root = ProductionManager.ensure_structure(project_name)
        return root / "assets" / asset_type

    @classmethod
    def list(cls, project_name: str, asset_type: str) -> list[dict[str, Any]]:
        folder = cls._folder(project_name, asset_type)
        assets: list[dict[str, Any]] = []
        for file in sorted(folder.glob("*.json")):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                data.setdefault("id", file.stem)
                data["_file"] = str(file)
                assets.append(data)
        return assets

    @classmethod
    def save(
        cls,
        project_name: str,
        asset_type: str,
        data: dict[str, Any],
    ) -> Path:
        name = str(data.get("name") or data.get("title") or data.get("id") or "asset").strip()
        if not name:
            raise ValueError("Asset name is required.")
        folder = cls._folder(project_name, asset_type)
        asset_id = str(data.get("id") or _slug(name))
        payload = dict(data)
        payload["id"] = asset_id
        payload["name"] = name
        payload.pop("_file", None)
        path = folder / f"{_slug(asset_id)}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    @classmethod
    def delete(cls, project_name: str, asset_type: str, asset_id: str) -> None:
        path = cls._folder(project_name, asset_type) / f"{_slug(asset_id)}.json"
        if path.exists():
            path.unlink()
