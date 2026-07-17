"""Business logic for production image assets."""
from __future__ import annotations

from movie.asset_database import AssetDatabase, ImageAssetVersion


class ImageAssetService:
    @staticmethod
    def list_versions(project_name: str, **filters) -> list[ImageAssetVersion]:
        return AssetDatabase(project_name).list_versions(**filters)

    @staticmethod
    def latest(project_name: str) -> list[ImageAssetVersion]:
        return AssetDatabase(project_name).latest_versions()

    @staticmethod
    def update_review(
        project_name: str,
        asset_id: str,
        version: int,
        *,
        status: str | None = None,
        rating: int | None = None,
        notes: str | None = None,
        tags: list[str] | None = None,
    ) -> None:
        AssetDatabase(project_name).update_review(
            asset_id, version, status=status, rating=rating, notes=notes, tags=tags
        )

    @staticmethod
    def summary(project_name: str) -> dict[str, int]:
        return AssetDatabase(project_name).summary()
