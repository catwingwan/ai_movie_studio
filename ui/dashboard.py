from nicegui import ui

from core import StudioCore, create_studio_core

from ui.panels.project_panel import ProjectPanel
from ui.panels.pipeline_panel import PipelinePanel
from ui.panels.character_panel import CharacterPanel
from ui.panels.story_panel import StoryPanel
from ui.panels.screenplay_panel import ScreenplayPanel
from ui.panels.scene_panel import ScenePanel
from ui.panels.storyboard_panel import StoryboardPanel
from ui.panels.director_panel import DirectorPanel
from ui.panels.jobs_panel import JobsPanel
from ui.panels.assets_panel import AssetsPanel
from ui.panels.character_bible_panel import CharacterBiblePanel
from ui.panels.location_bible_panel import LocationBiblePanel
from ui.panels.prop_library_panel import PropLibraryPanel
from ui.panels.prompt_builder_panel import PromptBuilderPanel
from ui.panels.comfyui_manager_panel import ComfyUIManagerPanel
from ui.panels.image_studio_panel import ImageStudioPanel
from ui.panels.image_assets_panel import ImageAssetsPanel
from ui.panels.production_board_panel import ProductionBoardPanel
from ui.panels.timeline_panel import TimelinePanel
from ui.panels.talent_department_panel import TalentDepartmentPanel


def build_dashboard(studio: StudioCore | None = None) -> StudioCore:
    """Build the interface and return the injected Studio Core."""

    studio = studio or create_studio_core()

    ui.colors(
        primary="#2563eb",
        secondary="#475569",
        positive="#16a34a",
        negative="#dc2626",
        warning="#d97706",
    )

    ui.add_head_html(
        """
        <style>
            html, body, #q-app {
                height: 100%;
                overflow: hidden;
            }

            body {
                background: #f8fafc;
            }

            .studio-shell {
                height: calc(100vh - 64px);
                min-height: 0;
                overflow: hidden;
            }

            .studio-sidebar {
                flex: 0 0 20rem;
                width: 20rem;
                height: 100%;
                min-height: 0;
                overflow-x: hidden;
                overflow-y: auto;
                overscroll-behavior: contain;
            }

            .studio-workspace {
                height: 100%;
                min-width: 0;
                min-height: 0;
                overflow-x: hidden;
                overflow-y: auto;
                overscroll-behavior: contain;
            }

            .studio-workspace .q-tab-panels,
            .studio-workspace .q-panel {
                overflow: visible;
            }

            .q-tab {
                text-transform: none;
            }
        </style>
        """
    )

    with ui.header().classes(
        "h-16 bg-slate-900 text-white "
        "items-center justify-between px-6"
    ):

        with ui.row().classes(
            "items-center gap-3"
        ):
            ui.icon("movie").classes("text-3xl")
            ui.label("AI Movie Studio").classes(
                "text-xl font-bold"
            )
            ui.badge("Local AI").props(
                "outline color=positive"
            )

        with ui.row().classes(
            "items-center gap-2"
        ):
            ui.label("Ollama").classes(
                "text-sm text-gray-300"
            )

            ui.icon("memory").classes(
                "text-green-400"
            )

    with ui.row().classes(
        "studio-shell w-full no-wrap gap-0"
    ):

        with ui.column().classes(
            "studio-sidebar w-80 "
            "bg-white border-r p-4 gap-4"
        ):

            project_panel = ProjectPanel()
            project_panel.studio = studio
            PipelinePanel(project_panel)
            ui.separator()
            JobsPanel()

        with ui.column().classes(
            "studio-workspace flex-grow p-6 gap-4"
        ):

            with ui.row().classes(
                "w-full items-center justify-between"
            ):

                with ui.column().classes("gap-0"):
                    ui.label("Workspace").classes(
                        "text-3xl font-bold"
                    )
                    ui.label(
                        "Create your movie from story "
                        "to final production."
                    ).classes(
                        "text-gray-500"
                    )

            tabs = ui.tabs().classes("w-full")

            with tabs:
                production_board_tab = ui.tab("Production Board", icon="dashboard")
                timeline_tab = ui.tab("Timeline", icon="timeline")
                talent_tab = ui.tab("Talent Department", icon="badge")
                character_tab = ui.tab(
                    "Characters",
                    icon="groups",
                )
                story_tab = ui.tab(
                    "Story",
                    icon="menu_book",
                )
                screenplay_tab = ui.tab(
                    "Screenplay",
                    icon="movie",
                )
                scenes_tab = ui.tab(
                    "Scenes",
                    icon="view_list",
                )
                storyboard_tab = ui.tab(
                    "Storyboard",
                    icon="photo_library",
                )
                director_tab = ui.tab(
                    "Director AI",
                    icon="rate_review",
                )
                character_bible_tab = ui.tab(
                    "Character Bible",
                    icon="face_retouching_natural",
                )
                location_bible_tab = ui.tab(
                    "Location Bible",
                    icon="location_city",
                )
                prop_library_tab = ui.tab(
                    "Prop Library",
                    icon="category",
                )
                prompt_builder_tab = ui.tab(
                    "Prompt Builder",
                    icon="auto_fix_high",
                )
                comfyui_tab = ui.tab(
                    "ComfyUI",
                    icon="hub",
                )
                image_studio_tab = ui.tab(
                    "Image Studio",
                    icon="image",
                )
                image_assets_tab = ui.tab(
                    "Image Assets",
                    icon="collections",
                )
                assets_tab = ui.tab(
                    "Assets",
                    icon="inventory_2",
                )

            with ui.tab_panels(
                tabs,
                value=production_board_tab,
            ).classes(
                "w-full bg-transparent"
            ):

                with ui.tab_panel(production_board_tab):
                    ProductionBoardPanel(project_panel)

                with ui.tab_panel(timeline_tab):
                    TimelinePanel(project_panel)

                with ui.tab_panel(talent_tab):
                    TalentDepartmentPanel(project_panel)

                with ui.tab_panel(character_tab):
                    CharacterPanel(project_panel)

                with ui.tab_panel(story_tab):
                    StoryPanel(project_panel)

                with ui.tab_panel(screenplay_tab):
                    ScreenplayPanel(project_panel)

                with ui.tab_panel(scenes_tab):
                    ScenePanel(project_panel)
                with ui.tab_panel(storyboard_tab):
                    StoryboardPanel(project_panel)

                with ui.tab_panel(director_tab):
                    DirectorPanel(project_panel)

                with ui.tab_panel(character_bible_tab):
                    CharacterBiblePanel(project_panel)

                with ui.tab_panel(location_bible_tab):
                    LocationBiblePanel(project_panel)

                with ui.tab_panel(prop_library_tab):
                    PropLibraryPanel(project_panel)

                with ui.tab_panel(prompt_builder_tab):
                    PromptBuilderPanel(project_panel)

                with ui.tab_panel(comfyui_tab):
                    ComfyUIManagerPanel(project_panel)

                with ui.tab_panel(image_studio_tab):
                    ImageStudioPanel(project_panel)

                with ui.tab_panel(image_assets_tab):
                    ImageAssetsPanel(project_panel)

                with ui.tab_panel(assets_tab):
                    AssetsPanel(project_panel)

    return studio
