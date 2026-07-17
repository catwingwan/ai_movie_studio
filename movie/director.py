"""Director AI orchestration with scene-by-scene persistence."""

from __future__ import annotations

from movie.director_ai import generate_director_review
from movie.director_schema import DirectorReview
from movie.director_storage import load_review, load_reviews, save_review
from movie.scene_storage import load_scenes
from movie.storyboard_storage import load_scene_shots


def generate_director_reviews(
    project_name: str,
    regenerate: bool = False,
) -> list[DirectorReview]:
    if not project_name.strip():
        raise ValueError("No project selected.")

    scenes = load_scenes(project_name)
    if not scenes:
        raise FileNotFoundError("Generate scenes before running Director AI.")

    for scene in scenes:
        existing = load_review(project_name, scene.scene_number)
        if existing and not regenerate:
            continue

        shots = load_scene_shots(project_name, scene.scene_number)
        if not shots:
            raise FileNotFoundError(
                f"Generate storyboard shots for scene {scene.scene_number} first."
            )

        review = generate_director_review(scene, shots)
        save_review(project_name, review)

    reviews = load_reviews(project_name)
    if not reviews:
        raise RuntimeError("No Director AI reviews were generated.")
    return reviews
