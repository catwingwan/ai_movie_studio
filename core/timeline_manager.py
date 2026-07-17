"""Read-only production timeline derived from scenes, storyboard and assets."""
from __future__ import annotations

from core.production_board import ProductionBoardManager


class TimelineManager:
    @staticmethod
    def build(project: str) -> list[dict]:
        timeline: list[dict] = []
        cursor = 0
        for scene in ProductionBoardManager.build(project):
            timeline.append(
                {
                    **scene.to_dict(),
                    "start_seconds": cursor,
                    "end_seconds": cursor + scene.duration_seconds,
                }
            )
            cursor += scene.duration_seconds
        return timeline

    @classmethod
    def total_duration(cls, project: str) -> int:
        timeline = cls.build(project)
        return timeline[-1]["end_seconds"] if timeline else 0
