"""Deterministic continuity checks for scenes and characters."""
from __future__ import annotations

from core.character_manager import CharacterManager
from core.timeline_manager import TimelineManager


class ContinuityManager:
    @staticmethod
    def inspect(project: str) -> list[dict]:
        issues: list[dict] = []
        for item in TimelineManager.build(project):
            if item["duration_seconds"] <= 0:
                issues.append({"severity": "warning", "scene_number": item["scene_number"],
                               "message": "Scene has no estimated duration."})
            if item.get("shot_count", item.get("storyboard_shots", 0)) == 0:
                issues.append({"severity": "warning", "scene_number": item["scene_number"],
                               "message": "Scene has no storyboard shots."})

        for character in CharacterManager.list_characters(project):
            previous = None
            for state in character.scene_states:
                if previous and not state.intentional_change:
                    if previous.wardrobe and state.wardrobe and previous.wardrobe.casefold() != state.wardrobe.casefold():
                        issues.append({
                            "severity": "warning", "type": "wardrobe",
                            "character": character.name, "scene_number": state.scene_number,
                            "message": f"Wardrobe changed from '{previous.wardrobe}' to '{state.wardrobe}'.",
                        })
                    if previous.emotion and state.emotion and previous.emotion.casefold() != state.emotion.casefold():
                        issues.append({
                            "severity": "info", "type": "emotion",
                            "character": character.name, "scene_number": state.scene_number,
                            "message": f"Emotion changes from '{previous.emotion}' to '{state.emotion}'. Confirm the story supports this transition.",
                        })
                previous = state
        return issues
