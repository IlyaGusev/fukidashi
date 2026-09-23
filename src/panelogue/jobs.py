import asyncio
import json
import mimetypes
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from panelogue.detect import detect_bytes

PAGES = Path("data/pages")
RESULTS = Path("data/results")
JOBS = Path("data/jobs")
ACTIVE = ("queued", "running")


@dataclass
class Step:
    page: str
    state: str = "queued"
    started: float | None = None
    finished: float | None = None
    boxes: int | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class Job:
    id: str
    kind: str
    name: str
    options: dict[str, Any]
    steps: list[Step]
    state: str = "queued"
    created: float = field(default_factory=time.time)
    started: float | None = None
    finished: float | None = None

    @property
    def active(self) -> bool:
        return self.state in ACTIVE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Job":
        return Job(**{**d, "steps": [Step(**s) for s in d["steps"]]})


class JobQueue:
    def __init__(self, workers: int) -> None:
        self.jobs: dict[str, Job] = {}
        self._workers = workers
        self._worker_tasks: list[asyncio.Task[None]] = []
        self._pending: asyncio.Queue[str] = asyncio.Queue()
        self._listeners: set[asyncio.Queue[dict[str, Any]]] = set()
        self._step_tasks: dict[str, asyncio.Task[list[str]]] = {}
        self._cancelled: set[str] = set()

    async def start(self) -> None:
        JOBS.mkdir(parents=True, exist_ok=True)
        for path in sorted(JOBS.glob("*.json")):
            job = Job.from_dict(json.loads(path.read_text()))
            if job.active:
                job.state = "interrupted"
                for step in job.steps:
                    if step.state in ACTIVE:
                        step.state = "interrupted"
                self._save(job)
            self.jobs[job.id] = job
        self._worker_tasks = [asyncio.create_task(self._worker()) for _ in range(self._workers)]

    async def stop(self) -> None:
        for task in self._worker_tasks:
            task.cancel()
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)

    def active_for(self, kind: str, name: str) -> Job | None:
        for job in self.jobs.values():
            if job.active and job.kind == kind and job.name == name:
                return job
        return None

    def submit(self, kind: str, name: str, pages: list[str], options: dict[str, Any]) -> Job:
        job = Job(uuid.uuid4().hex[:12], kind, name, options, [Step(p) for p in pages])
        self.jobs[job.id] = job
        self._emit(job)
        self._pending.put_nowait(job.id)
        return job

    def cancel(self, job: Job) -> None:
        if job.state == "queued":
            self._finish(job, cancelled=True)
        elif job.state == "running":
            self._cancelled.add(job.id)
            if task := self._step_tasks.get(job.id):
                task.cancel()

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        events: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._listeners.add(events)
        try:
            yield {"type": "snapshot", "jobs": [j.to_dict() for j in self.jobs.values()]}
            while True:
                try:
                    yield await asyncio.wait_for(events.get(), 15)
                except TimeoutError:
                    yield {"type": "ping"}
        finally:
            self._listeners.discard(events)

    def _publish(self, event: dict[str, Any]) -> None:
        for events in self._listeners:
            events.put_nowait(event)

    def _save(self, job: Job) -> None:
        (JOBS / f"{job.id}.json").write_text(json.dumps(job.to_dict()))

    def _emit(self, job: Job) -> None:
        self._save(job)
        self._publish({"type": "job", "job": job.to_dict()})

    def _finish(self, job: Job, cancelled: bool) -> None:
        for step in job.steps:
            if step.state == "queued":
                step.state = "cancelled"
        failed = all(s.state == "failed" for s in job.steps)
        job.state = "cancelled" if cancelled else "failed" if failed else "done"
        job.finished = time.time()
        self._cancelled.discard(job.id)
        self._emit(job)

    async def _worker(self) -> None:
        while True:
            job = self.jobs[await self._pending.get()]
            if job.state == "queued":
                await self._run(job)

    async def _run(self, job: Job) -> None:
        job.state = "running"
        job.started = time.time()
        self._emit(job)
        context: list[str] | None = None
        for i, step in enumerate(job.steps):
            if job.id in self._cancelled:
                break
            step.state = "running"
            step.started = time.time()
            self._emit(job)
            task = asyncio.create_task(self._run_step(job, i, context))
            self._step_tasks[job.id] = task
            try:
                context = await task
                step.state = "done"
            except asyncio.CancelledError:
                if job.id not in self._cancelled:
                    raise
                step.state = "cancelled"
            except Exception as e:  # noqa: BLE001
                step.state = "failed"
                step.error = f"{type(e).__name__}: {e}"
                context = None
            finally:
                step.finished = time.time()
                self._step_tasks.pop(job.id, None)
        self._finish(job, cancelled=job.id in self._cancelled)

    async def _run_step(self, job: Job, index: int, context: list[str] | None) -> list[str]:
        step = job.steps[index]
        path = PAGES / step.page
        mime = mimetypes.guess_type(path.name)[0] or "image/png"

        def on_progress(phase: str, chars: int) -> None:
            self._publish(
                {"type": "progress", "id": job.id, "step": index, "phase": phase, "chars": chars}
            )

        _, result = await detect_bytes(
            path.read_bytes(), mime, **job.options, context=context, on_progress=on_progress
        )
        (RESULTS / f"{step.page}.json").write_text(json.dumps(result, ensure_ascii=False))
        step.boxes = len(result["bubbles"])
        step.usage = result["usage"]
        return [b["text"] for b in result["bubbles"]]
