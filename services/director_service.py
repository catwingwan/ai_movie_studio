"""Service layer for Director AI reviews."""

from __future__ import annotations

from movie.director import generate_director_reviews
from movie.director_schema import DirectorReview
from movie.director_storage import load_reviews


class DirectorService:
    @staticmethod
    def generate(project_name: str) -> list[DirectorReview]:
        return generate_director_reviews(project_name, regenerate=False)

    @staticmethod
    def regenerate(project_name: str) -> list[DirectorReview]:
        return generate_director_reviews(project_name, regenerate=True)

    @staticmethod
    def load(project_name: str) -> list[DirectorReview]:
        return load_reviews(project_name)
