from pathlib import Path

from ai.provider import ask
from config.prompts import STORY_PROMPT
from config.logging import setup_logger
from config.settings import settings

logger = setup_logger("story")


print(">>> generate_story()")
def generate_story(
    project_name,
    title,
    genre,
    theme,
    characters=[]
):

    logger.info(
        "Generating story | project=%s | provider=%s | model=%s",
        project_name,
        settings.ai_provider,
        settings.ollama_model,
    )
    
    char_text = "\n".join(
        f"{c.get('name')} - {c.get('role')}"
        for c in characters
    )

    prompt = STORY_PROMPT.format(
        title=title,
        genre=genre,
        theme=theme,
        characters=char_text
    )

    story = ask(prompt)

    folder = Path("data/projects") / project_name
    folder.mkdir(parents=True, exist_ok=True)

    (folder / "story.md").write_text(
        story,
        encoding="utf-8"
    )

    logger.info("Story saved")

    return story