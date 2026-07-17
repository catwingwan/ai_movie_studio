"""Central project health, statistics, and production dependency inspection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from movie.project_manager import PROJECT_ROOT


@dataclass(frozen=True)
class ProductionStatistics:
    characters: int = 0
    scenes: int = 0
    shots: int = 0
    director_reviews: int = 0
    character_assets: int = 0
    location_assets: int = 0
    prop_assets: int = 0
    prompts: int = 0
    images: int = 0
    videos: int = 0
    exports: int = 0
    runtime_seconds: int = 0
    disk_bytes: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


class ProductionManager:
    """Single source of truth for production status and project statistics."""

    STAGES = (
        "Project",
        "Characters",
        "Story",
        "Screenplay",
        "Scenes",
        "Storyboard",
        "Director AI",
        "Character Bible",
        "Locations",
        "Props",
        "Prompts",
        "Images",
        "Videos",
        "Export",
    )

    ASSET_FOLDERS = (
        "assets/characters",
        "assets/locations",
        "assets/props",
        "assets/wardrobe",
        "assets/references",
    )

    PRODUCTION_FOLDERS = (
        "scenes",
        "storyboard",
        "director",
        "images",
        "videos",
        "audio",
        "exports",
        "prompts",
        *ASSET_FOLDERS,
    )

    @staticmethod
    def project_path(project_name: str) -> Path:
        if not project_name or Path(project_name).name != project_name:
            raise ValueError("Invalid project name.")
        return PROJECT_ROOT / project_name

    @classmethod
    def ensure_structure(cls, project_name: str) -> Path:
        root = cls.project_path(project_name)
        root.mkdir(parents=True, exist_ok=True)
        for relative in cls.PRODUCTION_FOLDERS:
            (root / relative).mkdir(parents=True, exist_ok=True)
        return root

    @staticmethod
    def _file_has_content(path: Path) -> bool:
        return path.exists() and path.is_file() and path.stat().st_size > 0

    @staticmethod
    def _json_list_count(path: Path) -> int:
        if not path.exists():
            return 0
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0
        return len(data) if isinstance(data, list) else 0

    @staticmethod
    def _count_files(path: Path, pattern: str = "*") -> int:
        if not path.exists():
            return 0
        return sum(1 for item in path.glob(pattern) if item.is_file())

    @staticmethod
    def _count_recursive(path: Path, pattern: str = "*") -> int:
        if not path.exists():
            return 0
        return sum(1 for item in path.rglob(pattern) if item.is_file())

    @staticmethod
    def _disk_usage(path: Path) -> int:
        if not path.exists():
            return 0
        total = 0
        for item in path.rglob("*"):
            try:
                if item.is_file():
                    total += item.stat().st_size
            except OSError:
                continue
        return total

    @staticmethod
    def _scene_runtime(path: Path) -> int:
        total = 0
        if not path.exists():
            return total
        for file in path.glob("scene_*.json"):
            try:
                data = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    value = data.get("duration_seconds", data.get("estimated_duration_seconds", 0))
                    total += max(0, int(value or 0))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
        return total

    @classmethod
    def get_statistics(cls, project_name: str) -> ProductionStatistics:
        root = cls.ensure_structure(project_name)
        assets = root / "assets"
        return ProductionStatistics(
            characters=cls._json_list_count(root / "characters.json"),
            scenes=cls._count_files(root / "scenes", "scene_*.json"),
            shots=cls._count_recursive(root / "storyboard", "shot_*.json"),
            director_reviews=cls._count_files(root / "director", "scene_*_review.json"),
            character_assets=cls._count_files(assets / "characters", "*.json"),
            location_assets=cls._count_files(assets / "locations", "*.json"),
            prop_assets=cls._count_files(assets / "props", "*.json"),
            prompts=cls._count_recursive(root / "prompts", "latest.json"),
            images=sum(cls._count_recursive(root / "images", pattern) for pattern in ("*.png", "*.jpg", "*.jpeg", "*.webp")),
            videos=cls._count_recursive(root / "videos", "*.mp4"),
            exports=cls._count_recursive(root / "exports", "*.mp4"),
            runtime_seconds=cls._scene_runtime(root / "scenes"),
            disk_bytes=cls._disk_usage(root),
        )

    @classmethod
    def get_status(cls, project_name: str) -> dict[str, bool]:
        root = cls.ensure_structure(project_name)
        stats = cls.get_statistics(project_name)
        return {
            "Project": cls._file_has_content(root / "project.json"),
            "Characters": stats.characters > 0,
            "Story": cls._file_has_content(root / "story.md"),
            "Screenplay": cls._file_has_content(root / "screenplay.md"),
            "Scenes": stats.scenes > 0,
            "Storyboard": stats.shots > 0,
            "Director AI": stats.director_reviews > 0,
            "Character Bible": stats.character_assets > 0,
            "Locations": stats.location_assets > 0,
            "Props": stats.prop_assets > 0,
            "Prompts": stats.prompts > 0,
            "Images": stats.images > 0,
            "Videos": stats.videos > 0,
            "Export": stats.exports > 0,
        }

    @classmethod
    def get_missing_assets(cls, project_name: str) -> list[str]:
        """Return human-readable production dependencies still missing."""
        status = cls.get_status(project_name)
        missing: list[str] = []
        dependency_labels = (
            "Characters",
            "Story",
            "Screenplay",
            "Scenes",
            "Storyboard",
            "Director AI",
            "Character Bible",
            "Locations",
        )
        for label in dependency_labels:
            if not status.get(label, False):
                missing.append(label)
        return missing

    @classmethod
    def get_health(cls, project_name: str) -> dict[str, Any]:
        status = cls.get_status(project_name)
        stats = cls.get_statistics(project_name)
        completed = sum(1 for complete in status.values() if complete)
        total = len(status)
        return {
            "project": project_name,
            "status": status,
            "statistics": stats.to_dict(),
            "missing_assets": cls.get_missing_assets(project_name),
            "completed_stages": completed,
            "total_stages": total,
            "progress": completed / total if total else 0.0,
        }
