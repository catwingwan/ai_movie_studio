"""Single-worker background job queue for local AI tasks."""

from __future__ import annotations

import queue
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class AIJob:
    id: str
    name: str
    project_name: str | None
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    message: str = "Waiting"
    created_at: str = field(default_factory=_utc_now)
    started_at: str | None = None
    finished_at: str | None = None
    result: Any = None
    error: str | None = None
    _callable: Callable[[], Any] | None = field(default=None, repr=False)

    def snapshot(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("_callable", None)
        data["status"] = self.status.value
        # Large generated results should not be copied into the Jobs UI.
        data["result"] = None
        return data


class JobQueue:
    """Thread-safe single-worker queue.

    One worker intentionally limits local AI concurrency to reduce memory pressure.
    """

    def __init__(self) -> None:
        self._pending: queue.Queue[str] = queue.Queue()
        self._jobs: dict[str, AIJob] = {}
        self._lock = threading.RLock()
        self._worker = threading.Thread(
            target=self._run_worker,
            name="ai-movie-studio-worker",
            daemon=True,
        )
        self._worker.start()

    def submit(
        self,
        name: str,
        function: Callable[..., Any],
        *args: Any,
        project_name: str | None = None,
        **kwargs: Any,
    ) -> str:
        job_id = uuid.uuid4().hex
        job = AIJob(
            id=job_id,
            name=name,
            project_name=project_name,
            _callable=lambda: function(*args, **kwargs),
        )
        with self._lock:
            self._jobs[job_id] = job
        self._pending.put(job_id)
        return job_id

    def get(self, job_id: str) -> AIJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def snapshots(self, limit: int = 30) -> list[dict[str, Any]]:
        with self._lock:
            jobs = sorted(
                self._jobs.values(),
                key=lambda item: item.created_at,
                reverse=True,
            )[:limit]
            return [job.snapshot() for job in jobs]

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status is not JobStatus.QUEUED:
                return False
            job.status = JobStatus.CANCELLED
            job.progress = 0
            job.message = "Cancelled"
            job.finished_at = _utc_now()
            return True

    def clear_finished(self) -> None:
        with self._lock:
            self._jobs = {
                job_id: job
                for job_id, job in self._jobs.items()
                if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}
            }

    def _run_worker(self) -> None:
        while True:
            job_id = self._pending.get()
            try:
                self._execute(job_id)
            finally:
                self._pending.task_done()

    def _execute(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status is JobStatus.CANCELLED:
                return
            job.status = JobStatus.RUNNING
            job.progress = 10
            job.message = "Running local AI task"
            job.started_at = _utc_now()
            function = job._callable

        try:
            if function is None:
                raise RuntimeError("Job has no executable function.")
            result = function()
        except Exception as error:  # noqa: BLE001 - preserve service errors for UI
            with self._lock:
                job.status = JobStatus.FAILED
                job.progress = 100
                job.message = "Failed"
                job.error = str(error)
                job.finished_at = _utc_now()
            return

        with self._lock:
            job.result = result
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.message = "Completed"
            job.finished_at = _utc_now()
            job._callable = None


job_queue = JobQueue()
