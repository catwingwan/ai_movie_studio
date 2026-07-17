"""Persistence helpers for Director AI reviews."""

from __future__ import annotations

import json
from pathlib import Path

from movie.director_schema import DirectorReview
from movie.project_manager import PROJECT_ROOT


def director_root(project_name: str) -> Path:
    return PROJECT_ROOT / project_name / "director"


def review_path(project_name: str, scene_number: int) -> Path:
    return director_root(project_name) / f"scene_{scene_number:03d}_review.json"


def save_review(project_name: str, review: DirectorReview) -> None:
    root = director_root(project_name)
    root.mkdir(parents=True, exist_ok=True)
    target = review_path(project_name, review.scene_number)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(review.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary.replace(target)


def load_review(project_name: str, scene_number: int) -> DirectorReview | None:
    path = review_path(project_name, scene_number)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid director review file: {path.name}")
    return DirectorReview.from_dict(
        data,
        scene_number=scene_number,
        scene_heading=str(data.get("scene_heading", "")),
    )


def load_reviews(project_name: str) -> list[DirectorReview]:
    root = director_root(project_name)
    if not root.exists():
        return []

    reviews: list[DirectorReview] = []
    for path in sorted(root.glob("scene_*_review.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        try:
            scene_number = int(data.get("scene_number", 0))
        except (TypeError, ValueError):
            continue
        if scene_number <= 0:
            continue
        reviews.append(
            DirectorReview.from_dict(
                data,
                scene_number=scene_number,
                scene_heading=str(data.get("scene_heading", "")),
            )
        )
    return sorted(reviews, key=lambda item: item.scene_number)
