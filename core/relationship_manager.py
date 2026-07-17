"""Deterministic character relationship graph."""
from __future__ import annotations

from movie.scene_storage import load_scenes


class RelationshipManager:
    @staticmethod
    def build(project: str) -> list[dict]:
        edges: dict[tuple[str, str, str], int] = {}
        for scene in load_scenes(project):
            characters = sorted({name.strip() for name in scene.characters if name.strip()})
            for index, source in enumerate(characters):
                for target in characters[index + 1:]:
                    key = (source, "shares_scene_with", target)
                    edges[key] = edges.get(key, 0) + 1
                if scene.location:
                    key = (source, "appears_in", scene.location)
                    edges[key] = edges.get(key, 0) + 1
        return [
            {"source": source, "relation": relation, "target": target, "weight": weight}
            for (source, relation, target), weight in sorted(edges.items())
        ]
