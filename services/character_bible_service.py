"""Service boundary for Character Bible generation and editing."""

from movie.character_bible import (
    generate_character_bibles,
    load_character_bibles,
    save_character_bible,
)


class CharacterBibleService:
    load = staticmethod(load_character_bibles)
    generate = staticmethod(generate_character_bibles)
    save = staticmethod(save_character_bible)
