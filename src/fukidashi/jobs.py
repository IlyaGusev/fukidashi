import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from dataclasses import asdict, dataclass, field
from typing import Any

import openai

from fukidashi.detect import BadOutput, Progress
from fukidashi.settings import settings
from fukidashi.store import translate_page, write_json

JOBS = settings.data_dir / "jobs"
ACTIVE = ("queued", "running")
RETRYABLE = (
    BadOutput,
    TimeoutError,
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)

Translate = Callable[
    [str, dict[str, Any], str | None, str | None, Progress], Awaitable[dict[str, Any]]
]


@dataclass
class Step:
    page: str
    state: str = "queued"
    attempts: int = 0
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

    @property
    def volume(self) -> str | None:
        return self.name if self.kind == "volume" else None

    @property
    def unfinished_pages(self) -> list[str]:
        return [s.page for s in self.steps if s.state != "done"]

    def duplicate_message(self) -> str:
        thinking = "thinking on" if self.options["thinking"] else "thinking off"
        settings = f"{self.options['model']}, {thinking}, {self.options['lang']}"
        return (
            f"{settings} is already {self.state} for this {self.kind}. "
            "Change a setting to queue another run."
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "Job":
        return Job(**{**d, "steps": [Step(**s) for s in d["steps"]]})


class JobQueue:
    def __init__(
        self,
        translate: Translate = translate_page,
        concurrency: int = 2,
        attempts: int = 3,
        step_timeout: float = 600,
        backoff: float = 2,
    ) -> None:
        self.jobs: dict[str, Job] = {}
        self.concurrency = concurrency
        self._translate = translate
        self._attempts = attempts
        self._step_timeout = step_timeout
        self._backoff = backoff
        self._slots = asyncio.Semaphore(concurrency)
        self._runners: dict[str, asyncio.Task[None]] = {}
        self._cancelled: set[str] = set()
        self._listeners: set[asyncio.Queue[dict[str, Any]]] = set()

    async def start(self) -> None:
        JOBS.mkdir(parents=True, exist_ok=True)
        jobs = [Job.from_dict(json.loads(p.read_text())) for p in JOBS.glob("*.json")]
        for job in sorted(jobs, key=lambda j: j.created):
            self.jobs[job.id] = job
            if job.active:
                for step in job.steps:
                    if step.state in ACTIVE:
                        step.state = "queued"
                self._launch(job)

    async def stop(self) -> None:
        for runner in self._runners.values():
            runner.cancel()
        await asyncio.gather(*self._runners.values(), return_exceptions=True)

    def active_for(self, kind: str, name: str, options: dict[str, Any]) -> Job | None:
        for job in self.jobs.values():
            if job.active and (job.kind, job.name, job.options) == (kind, name, options):
                return job
        return None

    def submit(self, kind: str, name: str, pages: list[str], options: dict[str, Any]) -> Job:
        job = Job(uuid.uuid4().hex[:12], kind, name, options, [Step(p) for p in pages])
        self.jobs[job.id] = job
        self._emit(job)
        self._launch(job)
        return job

    def retry(self, job: Job) -> Job:
        return self.submit(job.kind, job.name, job.unfinished_pages, job.options)

    def cancel(self, job: Job) -> None:
        if runner := self._runners.get(job.id):
            self._cancelled.add(job.id)
            runner.cancel()

    async def subscribe(self) -> AsyncIterator[dict[str, Any]]:
        events: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._listeners.add(events)
        try:
            yield {
                "type": "snapshot",
                "concurrency": self.concurrency,
                "jobs": [j.to_dict() for j in self.jobs.values()],
            }
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

    def _emit(self, job: Job) -> None:
        write_json(JOBS / f"{job.id}.json", job.to_dict())
        self._publish({"type": "job", "job": job.to_dict()})

    def _launch(self, job: Job) -> None:
        self._runners[job.id] = asyncio.create_task(self._run_job(job))

    async def _run_job(self, job: Job) -> None:
        try:
            async with asyncio.TaskGroup() as tg:
                previous: str | None = None
                for index, step in enumerate(job.steps):
                    if step.state == "queued":
                        tg.create_task(self._run_step(job, index, previous))
                    previous = step.page
        except asyncio.CancelledError:
            if job.id not in self._cancelled:
                raise
            for step in job.steps:
                if step.state in ACTIVE:
                    step.state = "cancelled"
                    step.finished = time.time()
        finally:
            self._runners.pop(job.id, None)
        self._finish(job)

    async def _run_step(self, job: Job, index: int, previous: str | None) -> None:
        step = job.steps[index]
        async with self._slots:
            self._begin(job, step)
            result = await self._attempt(job, step, previous, self._progress(job, index))
            self._end(job, step, result)

    async def _attempt(
        self, job: Job, step: Step, previous: str | None, on_progress: Progress
    ) -> dict[str, Any] | None:
        for attempt in range(1, self._attempts + 1):
            step.attempts = attempt
            try:
                async with asyncio.timeout(self._step_timeout):
                    return await self._translate(
                        step.page, job.options, previous, job.volume, on_progress
                    )
            except RETRYABLE as e:
                step.error = self._describe(e)
                self._emit(job)
                if attempt < self._attempts:
                    await asyncio.sleep(self._backoff * 2 ** (attempt - 1))
            except Exception as e:  # noqa: BLE001
                step.error = self._describe(e)
                return None
        return None

    def _describe(self, e: BaseException) -> str:
        if isinstance(e, TimeoutError):
            return f"no answer within {self._step_timeout:.0f}s"
        return f"{type(e).__name__}: {e}"

    def _begin(self, job: Job, step: Step) -> None:
        step.state = "running"
        step.started = time.time()
        if job.state == "queued":
            job.state = "running"
            job.started = time.time()
        self._emit(job)

    def _end(self, job: Job, step: Step, result: dict[str, Any] | None) -> None:
        if result is None:
            step.state = "failed"
        else:
            step.state = "done"
            step.error = None
            step.boxes = len(result["bubbles"])
            step.usage = result["usage"]
        step.finished = time.time()
        self._emit(job)

    def _finish(self, job: Job) -> None:
        if job.id in self._cancelled:
            job.state = "cancelled"
        elif any(s.state == "failed" for s in job.steps):
            job.state = "failed"
        else:
            job.state = "done"
        job.finished = time.time()
        self._cancelled.discard(job.id)
        self._emit(job)

    def _progress(self, job: Job, index: int) -> Progress:
        def on_progress(phase: str, chars: int) -> None:
            self._publish(
                {"type": "progress", "id": job.id, "step": index, "phase": phase, "chars": chars}
            )

        return on_progress
