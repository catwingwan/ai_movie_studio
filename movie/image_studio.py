"""Image Studio profiles, storage, and metadata."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from movie.production_manager import ProductionManager
from movie.asset_database import AssetDatabase, ImageAssetVersion


@dataclass(frozen=True, slots=True)
class ImageProfile:
    id: str
    name: str
    width: int
    height: int
    steps: int
    cfg: float
    retries: int = 1


PROFILES = (
    ImageProfile("draft", "Fast Draft", 768, 768, 16, 4.5, 1),
    ImageProfile("production", "Production", 1024, 1024, 24, 6.0, 2),
    ImageProfile("quality", "High Quality", 1024, 1024, 32, 7.0, 2),
)


def get_profile(profile_id: str) -> ImageProfile:
    return next((profile for profile in PROFILES if profile.id == profile_id), PROFILES[0])


@dataclass(slots=True)
class ImageRecord:
    scene_number: int
    shot_number: int
    filename: str
    prompt_id: str
    seed: int
    profile_id: str
    workflow_name: str
    checkpoint: str = ""
    prompt_version: int = 1
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "generated"
    source_filename: str = ""
    source_subfolder: str = ""
    source_type: str = "output"
    asset_id: str = ""
    version: int = 1
    rating: int = 0
    notes: str = ""
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ImageRecord":
        return cls(
            scene_number=max(1, int(data.get("scene_number", 1))),
            shot_number=max(1, int(data.get("shot_number", 1))),
            filename=str(data.get("filename", "")),
            prompt_id=str(data.get("prompt_id", "")),
            seed=int(data.get("seed", 0)),
            profile_id=str(data.get("profile_id", "draft")),
            workflow_name=str(data.get("workflow_name", "")),
            checkpoint=str(data.get("checkpoint", "")),
            prompt_version=max(1, int(data.get("prompt_version", 1))),
            generated_at=str(data.get("generated_at", "")),
            status=str(data.get("status", "generated")),
            source_filename=str(data.get("source_filename", "")),
            source_subfolder=str(data.get("source_subfolder", "")),
            source_type=str(data.get("source_type", "output")),
            asset_id=str(data.get("asset_id", "")),
            version=max(1, int(data.get("version", 1))),
            rating=max(0, min(5, int(data.get("rating", 0)))),
            notes=str(data.get("notes", "")),
            tags=[str(item) for item in data.get("tags", [])] if isinstance(data.get("tags", []), list) else [],
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def shot_image_folder(project_name: str, scene_number: int, shot_number: int) -> Path:
    folder = (
        ProductionManager.ensure_structure(project_name)
        / "images"
        / f"scene_{scene_number:03d}"
        / f"shot_{shot_number:03d}"
    )
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_image_result(
    project_name: str,
    record: ImageRecord,
    content: bytes,
    extension: str = ".png",
) -> Path:
    folder = shot_image_folder(project_name, record.scene_number, record.shot_number)
    existing = sorted(folder.glob("image_v*.*"))
    version = len([path for path in existing if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]) + 1
    extension = extension if extension.startswith(".") else f".{extension}"
    image_path = folder / f"image_v{version:03d}{extension.lower()}"
    temporary = image_path.with_suffix(image_path.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(image_path)
    record.filename = image_path.name
    record.version = version
    record.asset_id = record.asset_id or AssetDatabase.asset_id(record.scene_number, record.shot_number)
    metadata_path = folder / f"image_v{version:03d}.json"
    metadata_path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    latest_path = folder / "latest.json"
    latest_path.write_text(json.dumps(record.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    AssetDatabase(project_name).register(ImageAssetVersion(
        asset_id=record.asset_id,
        scene_number=record.scene_number,
        shot_number=record.shot_number,
        version=version,
        filename=record.filename,
        metadata_filename=metadata_path.name,
        status=record.status if record.status in {"draft", "review", "approved", "rejected", "archived"} else "draft",
        rating=record.rating,
        notes=record.notes,
        tags=record.tags,
        seed=record.seed,
        checkpoint=record.checkpoint,
        profile_id=record.profile_id,
        workflow_name=record.workflow_name,
        prompt_version=record.prompt_version,
        prompt_id=record.prompt_id,
        generated_at=record.generated_at,
    ))
    return image_path


def load_image_records(project_name: str) -> list[ImageRecord]:
    root = ProductionManager.ensure_structure(project_name) / "images"
    records: list[ImageRecord] = []
    for path in sorted(root.glob("scene_*/shot_*/latest.json")):
        try:
            records.append(ImageRecord.from_dict(json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return sorted(records, key=lambda item: (item.scene_number, item.shot_number))
