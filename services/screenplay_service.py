from movie.storage import read_story
from movie.screenplay import generate_screenplay


class ScreenplayService:

    @staticmethod
    def generate(project_name):

        story = read_story(project_name)

        return generate_screenplay(
            project_name,
            story
        )