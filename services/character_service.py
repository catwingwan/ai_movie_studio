"""Business logic for AI character generation and persistence."""

from __future__ import annotations

from typing import Any

from movie.character import load_characters, save_characters
from movie.character_ai import generate_characters
from movie.project_manager import load_project


class CharacterService:
    @staticmethod
    def generate(project_name: str) -> list[dict[str, Any]]:
        project = load_project(project_name)
        if project is None:
            raise FileNotFoundError(f"Project not found: {project_name}")

        characters = generate_characters(
            project.get("title", project_name),
            project.get("genre", "Drama"),
            project.get("theme", ""),
        )

        if not isinstance(characters, list) or not characters:
            raise ValueError("The AI did not return a valid character list.")

        cleaned: list[dict[str, Any]] = []
        for index, character in enumerate(characters, start=1):
            if not isinstance(character, dict):
                raise ValueError(f"Character {index} is not a JSON object.")

            name = str(character.get("name", "")).strip()
            if not name:
                raise ValueError(f"Character {index} has no name.")

            cleaned.append(
                {
                    "name": name,
                    "age": character.get("age", ""),
                    "role": str(character.get("role", "")).strip(),
                    "personality": str(character.get("personality", "")).strip(),
                    "goal": str(character.get("goal", "")).strip(),
                    "conflict": str(character.get("conflict", "")).strip(),
                }
            )

        save_characters(project_name, cleaned)
        return cleaned

    @staticmethod
    def load(project_name: str) -> list[dict[str, Any]]:
        data = load_characters(project_name)
        return data if isinstance(data, list) else []
