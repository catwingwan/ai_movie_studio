from movie.project_manager import load_project
from movie.character import load_characters
from movie.story import generate_story


class StoryService:


    @staticmethod
    def generate(project_name):

        print(">>> StoryService.generate() called")

        project = load_project(project_name)

        characters = load_characters(project_name)

        return generate_story(
            project_name,
            project["title"],
            project["genre"],
            project["theme"],
            characters
        )