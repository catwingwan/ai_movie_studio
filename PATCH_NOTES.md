# AI Movie Studio v0.7.2 - Talent Department + Continuity

## Install
Extract this archive over v0.7.1. Keep your `data/`, `venv/`, model files, and existing project assets.

## New
- Talent Department workspace
- Studio Core CharacterManager and RelationshipManager
- Character overview and appearance profile
- Editable wardrobe and emotion scene timelines
- Director notes per character
- Approved image reference discovery
- Inferred character/location relationships
- Deterministic wardrobe and emotion continuity warnings
- Character-related Studio Core events

## Storage
Editable talent production data is stored non-destructively in:

`data/projects/<project>/talent_state.json`

Existing Character Bible, scenes, images, and `assets.db` remain unchanged.
