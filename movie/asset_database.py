"""SQLite-backed production asset registry.

The database is an index over files already stored inside each project. Image files
remain portable and readable without SQLite; the registry adds versioning, review
states, notes, tags, and fast queries.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from movie.production_manager import ProductionManager


VALID_STATUSES = {"draft", "review", "approved", "rejected", "archived"}


@dataclass(slots=True)
class ImageAssetVersion:
    asset_id: str
    scene_number: int
    shot_number: int
    version: int
    filename: str
    metadata_filename: str
    status: str = "draft"
    rating: int = 0
    notes: str = ""
    tags: list[str] | None = None
    seed: int = 0
    checkpoint: str = ""
    profile_id: str = "draft"
    workflow_name: str = ""
    prompt_version: int = 1
    prompt_id: str = ""
    generated_at: str = ""

    def normalized_tags(self) -> list[str]:
        return sorted({tag.strip() for tag in (self.tags or []) if tag.strip()})


class AssetDatabase:
    """Project-local SQLite registry for production assets."""

    def __init__(self, project_name: str) -> None:
        self.project_name = project_name
        self.project_root = ProductionManager.ensure_structure(project_name)
        self.path = self.project_root / "assets.db"
        self._initialize()
        self._migrate_existing_metadata()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS image_assets (
                    asset_id TEXT PRIMARY KEY,
                    scene_number INTEGER NOT NULL,
                    shot_number INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(scene_number, shot_number)
                );

                CREATE TABLE IF NOT EXISTS image_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_id TEXT NOT NULL REFERENCES image_assets(asset_id) ON DELETE CASCADE,
                    version INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    metadata_filename TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    rating INTEGER NOT NULL DEFAULT 0,
                    notes TEXT NOT NULL DEFAULT '',
                    tags_json TEXT NOT NULL DEFAULT '[]',
                    seed INTEGER NOT NULL DEFAULT 0,
                    checkpoint TEXT NOT NULL DEFAULT '',
                    profile_id TEXT NOT NULL DEFAULT 'draft',
                    workflow_name TEXT NOT NULL DEFAULT '',
                    prompt_version INTEGER NOT NULL DEFAULT 1,
                    prompt_id TEXT NOT NULL DEFAULT '',
                    generated_at TEXT NOT NULL,
                    UNIQUE(asset_id, version)
                );

                CREATE INDEX IF NOT EXISTS idx_image_versions_status
                    ON image_versions(status);
                CREATE INDEX IF NOT EXISTS idx_image_versions_asset
                    ON image_versions(asset_id, version DESC);
                """
            )

    def _migrate_existing_metadata(self) -> None:
        """Index image metadata created before assets.db was introduced."""
        image_root = self.project_root / "images"
        for metadata_path in image_root.glob("scene_*/shot_*/image_v*.json"):
            try:
                data = json.loads(metadata_path.read_text(encoding="utf-8"))
                scene_number = int(data.get("scene_number", metadata_path.parents[1].name.split("_")[-1]))
                shot_number = int(data.get("shot_number", metadata_path.parent.name.split("_")[-1]))
                version = int(metadata_path.stem.rsplit("v", 1)[-1])
                filename = str(data.get("filename", ""))
                if not filename:
                    matches = list(metadata_path.parent.glob(f"image_v{version:03d}.*"))
                    filename = next((item.name for item in matches if item.suffix.lower() != ".json"), "")
                if not filename:
                    continue
                self.register(ImageAssetVersion(
                    asset_id=str(data.get("asset_id") or self.asset_id(scene_number, shot_number)),
                    scene_number=scene_number,
                    shot_number=shot_number,
                    version=version,
                    filename=filename,
                    metadata_filename=metadata_path.name,
                    status=str(data.get("status", "draft")),
                    rating=int(data.get("rating", 0) or 0),
                    notes=str(data.get("notes", "")),
                    tags=data.get("tags", []) if isinstance(data.get("tags", []), list) else [],
                    seed=int(data.get("seed", 0) or 0),
                    checkpoint=str(data.get("checkpoint", "")),
                    profile_id=str(data.get("profile_id", "draft")),
                    workflow_name=str(data.get("workflow_name", "")),
                    prompt_version=int(data.get("prompt_version", 1) or 1),
                    prompt_id=str(data.get("prompt_id", "")),
                    generated_at=str(data.get("generated_at", "")),
                ))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue

    @staticmethod
    def asset_id(scene_number: int, shot_number: int) -> str:
        return f"IMG-S{scene_number:03d}-SH{shot_number:03d}"

    def register(self, item: ImageAssetVersion) -> None:
        if item.status not in VALID_STATUSES:
            item.status = "draft"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute(
                """
                INSERT INTO image_assets(asset_id, scene_number, shot_number, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(asset_id) DO UPDATE SET updated_at=excluded.updated_at
                """,
                (item.asset_id, item.scene_number, item.shot_number, now, now),
            )
            db.execute(
                """
                INSERT INTO image_versions(
                    asset_id, version, filename, metadata_filename, status, rating,
                    notes, tags_json, seed, checkpoint, profile_id, workflow_name,
                    prompt_version, prompt_id, generated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(asset_id, version) DO UPDATE SET
                    filename=excluded.filename,
                    metadata_filename=excluded.metadata_filename,
                    seed=excluded.seed,
                    checkpoint=excluded.checkpoint,
                    profile_id=excluded.profile_id,
                    workflow_name=excluded.workflow_name,
                    prompt_version=excluded.prompt_version,
                    prompt_id=excluded.prompt_id,
                    generated_at=excluded.generated_at
                """,
                (
                    item.asset_id, item.version, item.filename, item.metadata_filename,
                    item.status, max(0, min(5, int(item.rating))), item.notes,
                    json.dumps(item.normalized_tags(), ensure_ascii=False), item.seed,
                    item.checkpoint, item.profile_id, item.workflow_name,
                    item.prompt_version, item.prompt_id, item.generated_at or now,
                ),
            )

    def list_versions(
        self,
        *,
        scene_number: int | None = None,
        shot_number: int | None = None,
        status: str | None = None,
        query: str = "",
    ) -> list[ImageAssetVersion]:
        clauses: list[str] = []
        values: list[object] = []
        if scene_number is not None:
            clauses.append("a.scene_number = ?")
            values.append(scene_number)
        if shot_number is not None:
            clauses.append("a.shot_number = ?")
            values.append(shot_number)
        if status and status != "all":
            clauses.append("v.status = ?")
            values.append(status)
        if query.strip():
            clauses.append("(v.notes LIKE ? OR v.tags_json LIKE ? OR v.checkpoint LIKE ?)")
            term = f"%{query.strip()}%"
            values.extend([term, term, term])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connect() as db:
            rows = db.execute(
                f"""
                SELECT a.asset_id, a.scene_number, a.shot_number,
                       v.version, v.filename, v.metadata_filename, v.status,
                       v.rating, v.notes, v.tags_json, v.seed, v.checkpoint,
                       v.profile_id, v.workflow_name, v.prompt_version,
                       v.prompt_id, v.generated_at
                FROM image_versions v
                JOIN image_assets a ON a.asset_id = v.asset_id
                {where}
                ORDER BY a.scene_number, a.shot_number, v.version DESC
                """,
                values,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def latest_versions(self) -> list[ImageAssetVersion]:
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT a.asset_id, a.scene_number, a.shot_number,
                       v.version, v.filename, v.metadata_filename, v.status,
                       v.rating, v.notes, v.tags_json, v.seed, v.checkpoint,
                       v.profile_id, v.workflow_name, v.prompt_version,
                       v.prompt_id, v.generated_at
                FROM image_assets a
                JOIN image_versions v ON v.asset_id = a.asset_id
                WHERE v.version = (
                    SELECT MAX(v2.version) FROM image_versions v2 WHERE v2.asset_id = a.asset_id
                )
                ORDER BY a.scene_number, a.shot_number
                """
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def update_review(
        self,
        asset_id: str,
        version: int,
        *,
        status: str | None = None,
        rating: int | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        assignments: list[str] = []
        values: list[object] = []
        with self.connect() as db:
            if status is not None:
                if status not in VALID_STATUSES:
                    raise ValueError(f"Unsupported asset status: {status}")
                if status == "approved":
                    db.execute(
                        "UPDATE image_versions SET status='archived' WHERE asset_id=? AND status='approved'",
                        (asset_id,),
                    )
                assignments.append("status = ?")
                values.append(status)
            if rating is not None:
                assignments.append("rating = ?")
                values.append(max(0, min(5, int(rating))))
            if notes is not None:
                assignments.append("notes = ?")
                values.append(notes.strip())
            if tags is not None:
                assignments.append("tags_json = ?")
                values.append(json.dumps(sorted({tag.strip() for tag in tags if tag.strip()})))
            if not assignments:
                return
            values.extend([asset_id, version])
            db.execute(
                f"UPDATE image_versions SET {', '.join(assignments)} WHERE asset_id=? AND version=?",
                values,
            )
            db.execute(
                "UPDATE image_assets SET updated_at=? WHERE asset_id=?",
                (datetime.now(timezone.utc).isoformat(), asset_id),
            )

    def summary(self) -> dict[str, int]:
        with self.connect() as db:
            row = db.execute(
                """
                SELECT COUNT(*) AS versions,
                       COUNT(DISTINCT asset_id) AS assets,
                       SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) AS approved,
                       SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) AS rejected,
                       SUM(CASE WHEN status='review' THEN 1 ELSE 0 END) AS review
                FROM image_versions
                """
            ).fetchone()
        return {key: int(row[key] or 0) for key in ("assets", "versions", "approved", "rejected", "review")}

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ImageAssetVersion:
        try:
            tags = json.loads(row["tags_json"] or "[]")
        except json.JSONDecodeError:
            tags = []
        return ImageAssetVersion(
            asset_id=row["asset_id"], scene_number=int(row["scene_number"]),
            shot_number=int(row["shot_number"]), version=int(row["version"]),
            filename=row["filename"], metadata_filename=row["metadata_filename"],
            status=row["status"], rating=int(row["rating"] or 0), notes=row["notes"] or "",
            tags=tags if isinstance(tags, list) else [], seed=int(row["seed"] or 0),
            checkpoint=row["checkpoint"] or "", profile_id=row["profile_id"] or "draft",
            workflow_name=row["workflow_name"] or "", prompt_version=int(row["prompt_version"] or 1),
            prompt_id=row["prompt_id"] or "", generated_at=row["generated_at"] or "",
        )

    def image_path(self, item: ImageAssetVersion) -> Path:
        return (
            self.project_root / "images" / f"scene_{item.scene_number:03d}"
            / f"shot_{item.shot_number:03d}" / item.filename
        )
