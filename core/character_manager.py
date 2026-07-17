"""Character production records for the Talent Department."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from movie.asset_database import AssetDatabase
from movie.character_bible import load_character_bibles
from movie.scene_storage import load_scenes
from movie.storage import project_path


@dataclass(slots=True)
class CharacterSceneState:
    scene_number: int
    wardrobe: str = ""
    emotion: str = ""
    notes: str = ""
    intentional_change: bool = False


@dataclass(slots=True)
class CharacterRecord:
    name: str
    role: str = ""
    status: str = "draft"
    personality: str = ""
    appearance: dict[str, str] = field(default_factory=dict)
    default_wardrobe: list[str] = field(default_factory=list)
    scene_numbers: list[int] = field(default_factory=list)
    reference_images: list[dict[str, Any]] = field(default_factory=list)
    director_notes: str = ""
    scene_states: list[CharacterSceneState] = field(default_factory=list)


class CharacterManager:
    """Build and persist character-centric production data."""

    @staticmethod
    def _state_file(project: str) -> Path:
        return project_path(project) / "talent_state.json"

    @classmethod
    def _load_state(cls, project: str) -> dict[str, Any]:
        path = cls._state_file(project)
        if not path.exists():
            return {"characters": {}}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"characters": {}}
        return data if isinstance(data, dict) else {"characters": {}}

    @classmethod
    def _save_state(cls, project: str, data: dict[str, Any]) -> None:
        path = cls._state_file(project)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def list_characters(cls, project: str) -> list[CharacterRecord]:
        bibles = load_character_bibles(project)
        scenes = load_scenes(project)
        state = cls._load_state(project).get("characters", {})
        if not isinstance(state, dict):
            state = {}

        records: list[CharacterRecord] = []
        for bible in bibles:
            scene_numbers = [
                scene.scene_number for scene in scenes
                if bible.name.casefold() in {name.casefold() for name in scene.characters}
            ]
            saved = state.get(bible.name, {}) if isinstance(state.get(bible.name, {}), dict) else {}
            raw_states = saved.get("scene_states", {})
            if not isinstance(raw_states, dict):
                raw_states = {}
            scene_states = []
            default_wardrobe = ", ".join(bible.default_wardrobe)
            for number in scene_numbers:
                item = raw_states.get(str(number), {})
                if not isinstance(item, dict):
                    item = {}
                scene_states.append(CharacterSceneState(
                    scene_number=number,
                    wardrobe=str(item.get("wardrobe", default_wardrobe)).strip(),
                    emotion=str(item.get("emotion", "")).strip(),
                    notes=str(item.get("notes", "")).strip(),
                    intentional_change=bool(item.get("intentional_change", False)),
                ))
            records.append(CharacterRecord(
                name=bible.name,
                role=bible.role,
                status=bible.status,
                personality=bible.personality,
                appearance={
                    "age": bible.age, "face": bible.face, "hair": bible.hair,
                    "eyes": bible.eyes, "skin_tone": bible.skin_tone,
                    "body_type": bible.body_type, "height": bible.height,
                },
                default_wardrobe=bible.default_wardrobe,
                scene_numbers=scene_numbers,
                reference_images=cls._approved_references(project, scene_numbers),
                director_notes=str(saved.get("director_notes", "")).strip(),
                scene_states=scene_states,
            ))
        return records

    @staticmethod
    def _approved_references(project: str, scene_numbers: list[int]) -> list[dict[str, Any]]:
        db = AssetDatabase(project)
        refs = []
        for item in db.list_versions(status="approved"):
            if item.scene_number in scene_numbers:
                refs.append({
                    "asset_id": item.asset_id,
                    "scene_number": item.scene_number,
                    "shot_number": item.shot_number,
                    "version": item.version,
                    "filename": item.filename,
                    "rating": item.rating,
                })
        return refs

    @classmethod
    def save_character(cls, project: str, name: str, *, director_notes: str, scene_states: list[dict[str, Any]]) -> None:
        data = cls._load_state(project)
        characters = data.setdefault("characters", {})
        record = characters.setdefault(name, {})
        record["director_notes"] = director_notes.strip()
        record["scene_states"] = {
            str(int(item["scene_number"])): {
                "wardrobe": str(item.get("wardrobe", "")).strip(),
                "emotion": str(item.get("emotion", "")).strip(),
                "notes": str(item.get("notes", "")).strip(),
                "intentional_change": bool(item.get("intentional_change", False)),
            }
            for item in scene_states
        }
        cls._save_state(project, data)
