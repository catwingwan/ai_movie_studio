from pathlib import Path
import json
from datetime import datetime

from movie.utils import slug

PROJECT_ROOT = Path("data/projects")


def create_project(title, genre, theme):

    folder = PROJECT_ROOT / slug(title)
    folder.mkdir(parents=True, exist_ok=True)

    project = {
        "title": title,
        "genre": genre,
        "theme": theme,
        "created": datetime.now().isoformat(),
        "story": "",
        "screenplay": "",
        "storyboard": ""
    }

    with open(folder / "project.json", "w") as f:
        json.dump(project, f, indent=4)

    return folder


def load_project(title):
    folder = PROJECT_ROOT / slug(title)
    file = folder / "project.json"

    if not file.exists():
        return None

    return json.load(open(file))