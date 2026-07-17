"""Character Bible orchestration and persistence."""

from __future__ import annotations

from typing import Any

from movie.asset_manager import AssetManager
from movie.character import load_characters
from movie.character_bible_ai import generate_character_bible
from movie.character_bible_schema import CharacterBible


def load_character_bibles(project_name: str) -> list[CharacterBible]:
    return [
        CharacterBible.from_dict(item, item)
        for item in AssetManager.list(project_name, "characters")
    ]


def generate_character_bibles(project_name: str) -> list[CharacterBible]:
    characters = load_characters(project_name)
    if not characters:
        raise ValueError("Generate characters before creating the Character Bible.")

    existing = {
        item.name.casefold(): item
        for item in load_character_bibles(project_name)
    }
    generated: list[CharacterBible] = []
    for character in characters:
        name = str(character.get("name", "")).strip()
        if not name:
            continue
        bible = existing.get(name.casefold())
        if bible is None:
            bible = generate_character_bible(character)
            AssetManager.save(project_name, "characters", bible.to_dict())
        generated.append(bible)
    if not generated:
        raise ValueError("No usable characters were available for Character Bible generation.")
    return generated


def save_character_bible(project_name: str, data: dict[str, Any]) -> CharacterBible:
    bible = CharacterBible.from_dict(data, data)
    AssetManager.save(project_name, "characters", bible.to_dict())
    return bible
