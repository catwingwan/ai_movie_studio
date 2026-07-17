"""Live local AI jobs and Ollama health panel."""

from __future__ import annotations

from nicegui import run, ui

from services.job_queue import JobStatus, job_queue
from services.ollama_health import OllamaHealthService


class JobsPanel:
    def __init__(self) -> None:
        with ui.row().classes("w-full items-center justify-between"):
            ui.label("⚙ AI Jobs").classes("text-xl font-bold")
            with ui.row().classes("gap-1"):
                ui.button(icon="delete_sweep", on_click=self.clear_finished).props(
                    "flat round"
                ).tooltip("Clear finished jobs")
                ui.button(icon="refresh", on_click=self.refresh_health).props(
                    "flat round"
                ).tooltip("Check Ollama")

        self.health_label = ui.label("Checking Ollama...").classes("text-sm text-gray-500")
        self.jobs_container = ui.column().classes("w-full gap-2")

        ui.timer(1.0, self.refresh_jobs)
        ui.timer(15.0, self.refresh_health)
        self.refresh_jobs()
        ui.timer(0.1, self.refresh_health, once=True)

    async def refresh_health(self) -> None:
        health = await run.io_bound(OllamaHealthService.check)
        self.health_label.set_text(health.message)
        self.health_label.classes(
            remove="text-gray-500 text-green-600 text-red-600 text-amber-600",
            add=(
                "text-green-600"
                if health.online and health.model_available
                else "text-amber-600" if health.online else "text-red-600"
            ),
        )

    def refresh_jobs(self) -> None:
        snapshots = job_queue.snapshots()
        self.jobs_container.clear()
        with self.jobs_container:
            if not snapshots:
                ui.label("No AI jobs yet.").classes("text-sm text-gray-500")
                return

            for job in snapshots:
                status = JobStatus(job["status"])
                icon = {
                    JobStatus.QUEUED: "schedule",
                    JobStatus.RUNNING: "hourglass_top",
                    JobStatus.COMPLETED: "check_circle",
                    JobStatus.FAILED: "error",
                    JobStatus.CANCELLED: "cancel",
                }[status]
                color = {
                    JobStatus.QUEUED: "text-gray-500",
                    JobStatus.RUNNING: "text-blue-600",
                    JobStatus.COMPLETED: "text-green-600",
                    JobStatus.FAILED: "text-red-600",
                    JobStatus.CANCELLED: "text-gray-400",
                }[status]

                with ui.card().classes("w-full shadow-none border p-3"):
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon(icon).classes(color)
                            with ui.column().classes("gap-0"):
                                ui.label(job["name"]).classes("font-medium")
                                detail = job.get("project_name") or "Global"
                                ui.label(f"{detail} · {job['status']}").classes(
                                    "text-xs text-gray-500"
                                )
                        if status is JobStatus.QUEUED:
                            ui.button(
                                icon="close",
                                on_click=lambda job_id=job["id"]: self.cancel(job_id),
                            ).props("flat round dense").tooltip("Cancel queued job")

                    ui.linear_progress(value=job["progress"] / 100).classes("w-full")
                    if job.get("error"):
                        ui.label(job["error"]).classes("text-xs text-red-600")

    def cancel(self, job_id: str) -> None:
        if job_queue.cancel(job_id):
            ui.notify("Queued job cancelled", type="warning")
        self.refresh_jobs()

    def clear_finished(self) -> None:
        job_queue.clear_finished()
        self.refresh_jobs()
