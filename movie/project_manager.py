from pathlib import Path
import json
import shutil

from movie.utils import slug

PROJECT_ROOT = Path("data/projects")
PROJECT_SUBFOLDERS = (
    "scenes",
    "storyboard",
    "director",
    "images",
    "videos",
    "audio",
    "exports",
    "assets/characters",
    "assets/locations",
    "assets/props",
    "assets/wardrobe",
    "assets/references",
)


def list_projects():
    PROJECT_ROOT.mkdir(parents=True, exist_ok=True)
    return sorted(p.name for p in PROJECT_ROOT.iterdir() if p.is_dir())


def create_project(title, genre, theme):
    folder = PROJECT_ROOT / slug(title)
    folder.mkdir(parents=True, exist_ok=True)
    for name in PROJECT_SUBFOLDERS:
        (folder / name).mkdir(exist_ok=True)

    data = {"title": title, "genre": genre, "theme": theme}
    (folder / "project.json").write_text(
        json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8"
    )
    return folder.name


def load_project(name):
    file = PROJECT_ROOT / name / "project.json"
    if not file.exists():
        return None
    return json.loads(file.read_text(encoding="utf-8"))


def delete_project(name):
    path = PROJECT_ROOT / name
    if path.exists():
        shutil.rmtree(path)


def add_characters(project_name, characters):
    file = PROJECT_ROOT / project_name / "characters.json"
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(
        json.dumps(characters, indent=4, ensure_ascii=False), encoding="utf-8"
    )
