"""Validated storyboard shot models for downstream image and video generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class StoryboardShot:
    id: str
    scene_number: int
    shot_number: int
    shot_type: str = "Medium Shot"
    camera_angle: str = "Eye Level"
    lens: str = "50mm"
    movement: str = "Static"
    composition: str = "Rule of Thirds"
    lighting: str = "Natural"
    mood: str = "Neutral"
    subject: str = ""
    action: str = ""
    duration_seconds: int = 4
    image_prompt: str = ""
    negative_prompt: str = ""
    status: str = "draft"

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        scene_number: int,
        default_shot_number: int,
    ) -> "StoryboardShot":
        raw_number = data.get("shot_number", data.get("shot", data.get("number", default_shot_number)))
        try:
            shot_number = max(1, int(raw_number))
        except (TypeError, ValueError):
            shot_number = default_shot_number

        raw_duration = data.get("duration_seconds", data.get("duration", 4))
        try:
            duration = max(1, min(30, int(raw_duration)))
        except (TypeError, ValueError):
            duration = 4

        shot_type = str(data.get("shot_type", data.get("camera", "Medium Shot"))).strip()
        image_prompt = str(data.get("image_prompt", data.get("prompt", ""))).strip()

        return cls(
            id=f"scene_{scene_number:03d}_shot_{shot_number:03d}",
            scene_number=scene_number,
            shot_number=shot_number,
            shot_type=shot_type or "Medium Shot",
            camera_angle=str(data.get("camera_angle", data.get("angle", "Eye Level"))).strip() or "Eye Level",
            lens=str(data.get("lens", "50mm")).strip() or "50mm",
            movement=str(data.get("movement", "Static")).strip() or "Static",
            composition=str(data.get("composition", "Rule of Thirds")).strip() or "Rule of Thirds",
            lighting=str(data.get("lighting", "Natural")).strip() or "Natural",
            mood=str(data.get("mood", "Neutral")).strip() or "Neutral",
            subject=str(data.get("subject", "")).strip(),
            action=str(data.get("action", data.get("description", ""))).strip(),
            duration_seconds=duration,
            image_prompt=image_prompt,
            negative_prompt=str(data.get("negative_prompt", "")).strip(),
            status=str(data.get("status", "draft")).strip() or "draft",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SceneStoryboard:
    scene_number: int
    scene_heading: str
    shots: list[StoryboardShot] = field(default_factory=list)

    @property
    def duration_seconds(self) -> int:
        return sum(shot.duration_seconds for shot in self.shots)
