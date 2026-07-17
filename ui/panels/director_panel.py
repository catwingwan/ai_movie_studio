"""Director AI review workspace."""

from __future__ import annotations

from nicegui import ui

from movie.director_schema import DirectorReview
from services.director_service import DirectorService
from ui.panels.base_content_panel import BaseContentPanel

DirectorReviewList = list[DirectorReview]


class DirectorPanel(BaseContentPanel[DirectorReviewList]):
    title = "Director AI"
    title_icon = "🎬"
    generate_label = "Run Director Review"
    generate_icon = "rate_review"
    select_message = "Select a project first."
    missing_message = "No director reviews yet. Generate the storyboard first."
    generating_message = "Local Director AI is reviewing scenes and shots..."
    success_notification = "Director review completed"

    def load_content(self, project_name: str) -> DirectorReviewList:
        return DirectorService.load(project_name)

    def generate_content(self, project_name: str) -> DirectorReviewList:
        return DirectorService.generate(project_name)

    def loaded_message(self, content: DirectorReviewList) -> str:
        return self._summary(content, "loaded")

    def generated_message(self, content: DirectorReviewList) -> str:
        return self._summary(content, "generated")

    @staticmethod
    def _summary(content: DirectorReviewList, verb: str) -> str:
        average = sum(item.overall_score for item in content) / len(content)
        return f"{len(content)} scene reviews {verb} · average score {average:.1f}/5."

    @staticmethod
    def _score_badge(label: str, score: int) -> None:
        color = "positive" if score >= 4 else "warning" if score == 3 else "negative"
        ui.badge(f"{label}: {score}/5").props(f"outline color={color}")

    @staticmethod
    def _render_list(title: str, items: list[str], icon: str) -> None:
        if not items:
            return
        with ui.expansion(title, icon=icon).classes("w-full"):
            for item in items:
                with ui.row().classes("items-start gap-2 no-wrap"):
                    ui.icon("chevron_right").classes("text-gray-400 mt-1")
                    ui.label(item).classes("text-sm")

    def render_content(self, content: DirectorReviewList) -> None:
        self.output.clear()
        average = sum(item.overall_score for item in content) / len(content)

        with self.output:
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(f"{len(content)} scenes reviewed").classes(
                    "text-lg font-semibold"
                )
                ui.badge(f"Average {average:.1f}/5").props("outline color=primary")

            for review in content:
                with ui.card().classes("w-full shadow-none border rounded-xl"):
                    with ui.row().classes("w-full items-center justify-between gap-4"):
                        with ui.column().classes("gap-0"):
                            ui.label(f"Scene {review.scene_number:02d}").classes(
                                "text-xs font-bold uppercase tracking-wide text-blue-600"
                            )
                            ui.label(review.scene_heading or "Untitled Scene").classes(
                                "text-xl font-bold"
                            )
                        ui.badge(f"Overall {review.overall_score}/5").props(
                            "outline color=primary"
                        )

                    with ui.row().classes("gap-2 flex-wrap"):
                        self._score_badge("Emotion", review.emotion_score)
                        self._score_badge("Pacing", review.pacing_score)
                        self._score_badge("Dialogue", review.dialogue_score)
                        self._score_badge("Visual", review.visual_interest_score)
                        self._score_badge("Continuity", review.continuity_score)

                    if review.director_note:
                        with ui.card().classes(
                            "w-full bg-blue-50 shadow-none border border-blue-100"
                        ):
                            ui.label("Director Note").classes(
                                "text-xs font-bold uppercase text-blue-700"
                            )
                            ui.label(review.director_note).classes("text-sm")

                    self._render_list("Strengths", review.strengths, "thumb_up")
                    self._render_list("Concerns", review.concerns, "warning")
                    self._render_list(
                        "Recommended Improvements",
                        review.recommendations,
                        "auto_fix_high",
                    )
                    self._render_list(
                        "Shot Recommendations",
                        review.shot_recommendations,
                        "videocam",
                    )
                    self._render_list(
                        "Sound Recommendations",
                        review.sound_recommendations,
                        "graphic_eq",
                    )
