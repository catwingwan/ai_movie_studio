"""Screenplay generation and persistence."""

from __future__ import annotations

from ai.provider import ask
from config.logging import setup_logger
from config.prompts import SCREENPLAY_PROMPT
from movie.storage import write_screenplay

logger = setup_logger("screenplay")


def generate_screenplay(project_name: str, story: str) -> str:
    if not project_name or not project_name.strip():
        raise ValueError("No project selected.")

    if not story or not story.strip():
        raise ValueError("Story is empty. Generate a story first.")

    logger.info("Generating screenplay | project=%s", project_name)

    prompt = SCREENPLAY_PROMPT.format(story=story)
    screenplay = ask(prompt)

    if screenplay is None:
        raise RuntimeError("The local AI returned no screenplay response.")

    screenplay = str(screenplay).strip()
    if not screenplay:
        raise RuntimeError("The local AI returned an empty screenplay.")

    screenplay_file = write_screenplay(project_name, screenplay)
    logger.info("Screenplay saved | path=%s", screenplay_file)
    return screenplay
