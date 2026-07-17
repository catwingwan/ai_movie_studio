"""Deterministic master prompt composition from production assets."""
from __future__ import annotations

from movie.asset_manager import AssetManager
from movie.director_storage import load_review
from movie.prompt_schema import PromptRecord
from movie.prompt_storage import next_version, save_prompt
from movie.prompt_validator import validate_prompt
from movie.scene_storage import load_scenes
from movie.storyboard_storage import load_storyboards
from movie.style_manager import StyleManager


def _asset_text(asset: dict, fields: tuple[str, ...]) -> str:
    parts: list[str] = []
    for field in fields:
        value = asset.get(field)
        if isinstance(value, list):
            value = ", ".join(str(item) for item in value if str(item).strip())
        text = str(value or "").strip()
        if text and text not in parts:
            parts.append(text)
    return ", ".join(parts)


def _match_characters(assets: list[dict], haystack: str) -> list[dict]:
    lower = haystack.lower()
    matched = [asset for asset in assets if str(asset.get("name", "")).strip().lower() in lower]
    return matched


def _match_location(assets: list[dict], location: str) -> dict | None:
    wanted = location.strip().lower()
    if not wanted:
        return None
    for asset in assets:
        name = str(asset.get("name", "")).strip().lower()
        if name == wanted or name in wanted or wanted in name:
            return asset
    return None


def _match_props(assets: list[dict], scene_number: int, haystack: str) -> list[dict]:
    lower = haystack.lower()
    matched: list[dict] = []
    for asset in assets:
        scenes = asset.get("scenes", [])
        name = str(asset.get("name", "")).strip()
        if scene_number in scenes or (name and name.lower() in lower):
            matched.append(asset)
    return matched


def build_project_prompts(project_name: str, style_id: str | None = None) -> list[PromptRecord]:
    style_id = style_id or StyleManager.get_project_style(project_name)
    StyleManager.set_project_style(project_name, style_id)
    style = StyleManager.get(style_id)

    characters = AssetManager.list(project_name, "characters")
    locations = AssetManager.list(project_name, "locations")
    props = AssetManager.list(project_name, "props")
    scenes = {scene.scene_number: scene for scene in load_scenes(project_name)}
    storyboards = load_storyboards(project_name)
    if not storyboards:
        raise ValueError("No storyboard shots found. Generate the storyboard first.")

    records: list[PromptRecord] = []
    for board in storyboards:
        scene = scenes.get(board.scene_number)
        location_name = scene.location if scene else ""
        location_asset = _match_location(locations, location_name)
        review = load_review(project_name, board.scene_number)
        director_note = review.director_note if review else ""

        for shot in board.shots:
            haystack = " ".join(
                [shot.subject, shot.action, shot.image_prompt, " ".join(scene.characters) if scene else "", scene.summary if scene else "", scene.action if scene else ""]
            )
            character_assets = _match_characters(characters, haystack)
            prop_assets = _match_props(props, board.scene_number, haystack)

            sections: list[str] = [style.prompt_prefix]
            if character_assets:
                sections.append(
                    "Characters: " + "; ".join(
                        f"{asset.get('name')}: " + _asset_text(
                            asset,
                            ("consistency_prompt", "face", "hair", "eyes", "skin_tone", "body_type", "default_wardrobe"),
                        )
                        for asset in character_assets
                    )
                )
            elif shot.subject:
                sections.append(f"Subject: {shot.subject}")

            if location_asset:
                sections.append(
                    f"Location: {location_asset.get('name')}: "
                    + _asset_text(location_asset, ("consistency_prompt", "architecture", "layout", "lighting", "atmosphere", "color_palette"))
                )
            elif location_name:
                sections.append(f"Location: {location_name}")

            if prop_assets:
                sections.append(
                    "Props: " + "; ".join(
                        f"{asset.get('name')}: " + _asset_text(asset, ("consistency_prompt", "description", "materials", "colors", "condition"))
                        for asset in prop_assets
                    )
                )

            sections.extend(
                [
                    f"Shot action: {shot.action or shot.subject}",
                    f"Camera: {shot.shot_type}, {shot.camera_angle}, {shot.lens} lens, {shot.movement}",
                    f"Composition: {shot.composition}",
                    f"Lighting: {shot.lighting}; style guidance: {style.lighting}",
                    f"Mood: {shot.mood}",
                    f"Color and contrast: {style.color_palette}; {style.contrast}; {style.depth_of_field}",
                ]
            )
            if director_note:
                sections.append(f"Director note: {director_note}")
            if shot.image_prompt:
                sections.append(f"Storyboard visual intent: {shot.image_prompt}")
            sections.append(style.prompt_suffix)

            negatives = [
                "text, captions, subtitles, logo, watermark, duplicate people, malformed hands, malformed anatomy",
                style.negative_prompt,
                shot.negative_prompt,
            ]
            for asset in character_assets + ([location_asset] if location_asset else []) + prop_assets:
                value = str(asset.get("negative_prompt", "")).strip()
                if value:
                    negatives.append(value)

            record = PromptRecord(
                id=f"scene_{board.scene_number:03d}_shot_{shot.shot_number:03d}",
                scene_number=board.scene_number,
                shot_number=shot.shot_number,
                style_id=style.id,
                prompt=". ".join(section.strip(" .") for section in sections if section.strip()) + ".",
                negative_prompt=", ".join(dict.fromkeys(item for item in negatives if item)),
                character_names=[str(asset.get("name")) for asset in character_assets],
                location_name=str(location_asset.get("name")) if location_asset else location_name,
                prop_names=[str(asset.get("name")) for asset in prop_assets],
                director_note=director_note,
                version=next_version(project_name, board.scene_number, shot.shot_number),
            )
            score, warnings = validate_prompt(record)
            record.quality_score = score
            record.warnings = warnings
            save_prompt(project_name, record)
            records.append(record)
    return records
