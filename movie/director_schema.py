"""Validated Director AI review models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _score(value: Any, default: int = 3) -> int:
    try:
        return max(1, min(5, int(value)))
    except (TypeError, ValueError):
        return default


def _text_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


@dataclass(slots=True)
class DirectorReview:
    scene_number: int
    scene_heading: str
    overall_score: int = 3
    emotion_score: int = 3
    pacing_score: int = 3
    dialogue_score: int = 3
    visual_interest_score: int = 3
    continuity_score: int = 3
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    shot_recommendations: list[str] = field(default_factory=list)
    sound_recommendations: list[str] = field(default_factory=list)
    director_note: str = ""
    status: str = "reviewed"

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        scene_number: int,
        scene_heading: str,
    ) -> "DirectorReview":
        return cls(
            scene_number=scene_number,
            scene_heading=scene_heading,
            overall_score=_score(data.get("overall_score")),
            emotion_score=_score(data.get("emotion_score")),
            pacing_score=_score(data.get("pacing_score")),
            dialogue_score=_score(data.get("dialogue_score")),
            visual_interest_score=_score(data.get("visual_interest_score")),
            continuity_score=_score(data.get("continuity_score")),
            strengths=_text_list(data.get("strengths")),
            concerns=_text_list(data.get("concerns")),
            recommendations=_text_list(data.get("recommendations")),
            shot_recommendations=_text_list(data.get("shot_recommendations")),
            sound_recommendations=_text_list(data.get("sound_recommendations")),
            director_note=str(data.get("director_note", "")).strip(),
            status=str(data.get("status", "reviewed")).strip() or "reviewed",
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
