"""Production board snapshots derived from project files and asset approvals."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path

from movie.asset_database import AssetDatabase
from movie.production_manager import ProductionManager


@dataclass(frozen=True, slots=True)
class SceneProductionStatus:
    scene_number: int
    heading: str
    duration_seconds: int
    shots: int
    prompts: int
    generated_images: int
    approved_images: int
    videos: int

    @property
    def image_progress(self) -> float:
        return min(1.0, self.approved_images / self.shots) if self.shots else 0.0

    @property
    def production_progress(self) -> float:
        if not self.shots:
            return 0.0
        # Prompt, image generation, approval and video are equal production gates.
        prompt_ratio = min(1.0, self.prompts / self.shots)
        image_ratio = min(1.0, self.generated_images / self.shots)
        approval_ratio = min(1.0, self.approved_images / self.shots)
        video_ratio = min(1.0, self.videos / self.shots)
        return (prompt_ratio + image_ratio + approval_ratio + video_ratio) / 4

    @property
    def state(self) -> str:
        if self.shots and self.videos >= self.shots:
            return "complete"
        if self.generated_images or self.prompts:
            return "in_progress"
        if self.shots:
            return "ready"
        return "blocked"

    def to_dict(self) -> dict:
        data = asdict(self)
        data.update(
            image_progress=self.image_progress,
            production_progress=self.production_progress,
            state=self.state,
        )
        return data


class ProductionBoardManager:
    @staticmethod
    def _json(path: Path) -> dict:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    @classmethod
    def build(cls, project: str) -> list[SceneProductionStatus]:
        root = ProductionManager.ensure_structure(project)
        database = AssetDatabase(project)
        latest = database.latest_versions()
        latest_by_scene: dict[int, list] = {}
        for version in latest:
            latest_by_scene.setdefault(version.scene_number, []).append(version)

        rows: list[SceneProductionStatus] = []
        for index, scene_path in enumerate(sorted((root / "scenes").glob("scene_*.json")), start=1):
            scene = cls._json(scene_path)
            number = int(scene.get("scene_number") or scene.get("number") or index)
            storyboard_dir = root / "storyboard" / f"scene_{number:03d}"
            prompt_dir = root / "prompts" / f"scene_{number:03d}"
            video_dir = root / "videos" / f"scene_{number:03d}"
            scene_versions = latest_by_scene.get(number, [])
            rows.append(
                SceneProductionStatus(
                    scene_number=number,
                    heading=str(scene.get("heading") or scene.get("title") or f"Scene {number}"),
                    duration_seconds=max(0, int(scene.get("duration_seconds") or scene.get("estimated_duration_seconds") or 0)),
                    shots=sum(1 for p in storyboard_dir.glob("shot_*.json") if p.is_file()),
                    prompts=sum(1 for p in prompt_dir.glob("shot_*/latest.json") if p.is_file()),
                    generated_images=len(scene_versions),
                    approved_images=sum(1 for item in scene_versions if item.status == "approved"),
                    videos=sum(1 for p in video_dir.rglob("*.mp4") if p.is_file()) if video_dir.exists() else 0,
                )
            )
        return rows

    @classmethod
    def summary(cls, project: str) -> dict:
        scenes = cls.build(project)
        shots = sum(item.shots for item in scenes)
        approved = sum(item.approved_images for item in scenes)
        generated = sum(item.generated_images for item in scenes)
        videos = sum(item.videos for item in scenes)
        runtime = sum(item.duration_seconds for item in scenes)
        progress = sum(item.production_progress for item in scenes) / len(scenes) if scenes else 0.0
        return {
            "scenes": len(scenes),
            "shots": shots,
            "generated_images": generated,
            "approved_images": approved,
            "videos": videos,
            "runtime_seconds": runtime,
            "progress": progress,
        }
