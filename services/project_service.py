from movie.project_manager import (
    create_project,
    delete_project,
    list_projects,
    load_project,
)


class ProjectService:

    @staticmethod
    def create(title, genre, theme):

        return create_project(
            title,
            genre,
            theme
        )

    @staticmethod
    def load(project):

        return load_project(project)

    @staticmethod
    def list():

        return list_projects()

    @staticmethod
    def delete(project):

        delete_project(project)