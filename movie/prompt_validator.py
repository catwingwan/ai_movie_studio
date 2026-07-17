"""Rule-based prompt completeness scoring."""
from __future__ import annotations

from movie.prompt_schema import PromptRecord


def validate_prompt(record: PromptRecord) -> tuple[int, list[str]]:
    score = 100
    warnings: list[str] = []
    checks = (
        (bool(record.character_names), 12, "No matched Character Bible for this shot."),
        (bool(record.location_name), 12, "No matched Location Bible for this scene."),
        (len(record.prompt) >= 180, 15, "Prompt is too short for consistent image generation."),
        (bool(record.negative_prompt), 10, "Negative prompt is empty."),
        ("camera" in record.prompt.lower() or "lens" in record.prompt.lower(), 10, "Camera or lens detail is missing."),
        ("lighting" in record.prompt.lower() or "light" in record.prompt.lower(), 10, "Lighting detail is missing."),
        (bool(record.director_note), 6, "No Director AI note is available for this scene."),
    )
    for passed, deduction, warning in checks:
        if not passed:
            score -= deduction
            warnings.append(warning)
    return max(0, score), warnings
