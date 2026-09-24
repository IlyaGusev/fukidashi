import asyncio
import time
import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import openai

from fukidashi.detect import BadOutput, Progress, detect_file
from fukidashi.store import Store

ACTIVE = ("queued", "running")
ACTIVE_SQL = "(" + ", ".join(f"'{s}'" for s in ACTIVE) + ")"
RETRYABLE = (
    BadOutput,
    TimeoutError,
    openai.APIConnectionError,
    openai.RateLimitError,
    openai.InternalServerError,
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY, volume INTEGER NOT NULL REFERENCES volumes(id) ON DELETE CASCADE,
    model TEXT NOT NULL, thinking INTEGER NOT NULL, lang TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'queued', created REAL NOT NULL, started REAL, finished REAL);
CREATE TABLE IF NOT EXISTS steps (
    job TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE, position INTEGER NOT NULL,
    page INTEGER REFERENCES pages(id) ON DELETE SET NULL,
    state TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
    started REAL, finished REAL, translation INTEGER, tokens INTEGER, error TEXT,
    PRIMARY KEY (job, position));
CREATE INDEX IF NOT EXISTS steps_state ON steps(state);
"""
CLAIM = """
UPDATE steps SET state = 'running', started = ?, attempts = 0, error = NULL
WHERE (job, position) = (
    SELECT s.job, s.position FROM steps s JOIN jobs j ON j.id = s.job
    WHERE s.state = 'queued'
    ORDER BY (SELECT count(*) FROM steps WHERE job = j.id) > 1, j.created, s.position LIMIT 1)
RETURNING job, position, page
"""
FINISH_JOB = f"""
UPDATE jobs SET finished = ?, state = CASE
    WHEN EXISTS (SELECT 1 FROM steps WHERE job = jobs.id AND state = 'failed') THEN 'failed'
    ELSE 'done' END
WHERE id = ? AND state = 'running'
  AND NOT EXISTS (SELECT 1 FROM steps WHERE job = jobs.id AND state IN {ACTIVE_SQL})
"""
JOB_LIST = "SELECT j.*, v.title FROM jobs j LEFT JOIN volumes v ON v.id = j.volume"
STEP_LIST = (
    "SELECT s.*, p.file FROM steps s LEFT JOIN pages p ON p.id = s.page "
    "WHERE s.job = ? ORDER BY s.position"
)

Translate = Callable[[Path, dict[str, Any], list[str] | None, Progress], Awaitable[dict[str, Any]]]
StepKey = tuple[str, int]


class Duplicate(Exception):
    pass


def job_options(job: dict[str, Any]) -> dict[str, Any]:
    return {"model": job["model"], "thinking": job["thinking"], "lang": job["lang"]}


def duplicate_message(job: dict[str, Any]) -> str:
    thinking = "thinking on" if job["thinking"] else "thinking off"
    return (
        f"{job['model']}, {thinking}, {job['lang']} is already {job['state']} "
        "for these pages. Change a setting to queue another run."
    )


def placeholders(values: list[int]) -> str:
    return "(" + ", ".join("?" * len(values)) + ")"


class JobQueue:
    def __init__(
        self,
        store: Store,
        translate: Translate = detect_file,
        concurrency: int = 2,
        attempts: int = 3,
        step_timeout: float = 600,
        backoff: float = 2,
    ) -> None:
        self._store = store
        self._db = store.db
        self._translate = translate
        self._concurrency = concurrency
        self._attempts = attempts
        self._step_timeout = step_timeout
        self._backoff = backoff
        self._workers: list[asyncio.Task[None]] = []
        self._running: dict[StepKey, asyncio.Task[dict[str, Any] | None]] = {}
        self._progress: dict[StepKey, tuple[str, int]] = {}
        self._wake = asyncio.Event()
        self._db.executescript(SCHEMA)

    async def start(self) -> None:
        self._db.execute("UPDATE steps SET state = 'queued' WHERE state = 'running'")
        self._workers = [asyncio.create_task(self._work()) for _ in range(self._concurrency)]
        self._wake.set()

    async def stop(self) -> None:
        for task in [*self._workers, *self._running.values()]:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)

    def list_jobs(self, limit: int = 30) -> list[dict[str, Any]]:
        rows = self._db.execute(f"{JOB_LIST} ORDER BY j.created DESC LIMIT ?", (limit,))
        return [self._with_steps(dict(r)) for r in rows]

    def get(self, job_id: str) -> dict[str, Any] | None:
        row = self._db.execute(f"{JOB_LIST} WHERE j.id = ?", (job_id,)).fetchone()
        return self._with_steps(dict(row)) if row else None

    def busy(self, pages: list[int]) -> bool:
        row = self._db.execute(
            f"SELECT 1 FROM steps WHERE state IN {ACTIVE_SQL} AND page IN {placeholders(pages)}",
            pages,
        ).fetchone()
        return row is not None

    def active_for(self, pages: list[int], options: dict[str, Any]) -> dict[str, Any] | None:
        row = self._db.execute(
            f"{JOB_LIST} JOIN steps s ON s.job = j.id WHERE s.state IN {ACTIVE_SQL} "
            f"AND s.page IN {placeholders(pages)} "
            "AND j.model = ? AND j.thinking = ? AND j.lang = ? LIMIT 1",
            (*pages, options["model"], options["thinking"], options["lang"]),
        ).fetchone()
        return self._with_steps(dict(row)) if row else None

    def submit(self, volume: int, pages: list[int], options: dict[str, Any]) -> dict[str, Any]:
        if duplicate := self.active_for(pages, options):
            raise Duplicate(duplicate_message(duplicate))
        job_id = uuid.uuid4().hex[:12]
        self._db.execute("BEGIN")
        self._db.execute(
            "INSERT INTO jobs (id, volume, model, thinking, lang, created) "
            "VALUES (:id, :volume, :model, :thinking, :lang, :created)",
            {"id": job_id, "volume": volume, "created": time.time(), **options},
        )
        self._db.executemany(
            "INSERT INTO steps (job, position, page) VALUES (?, ?, ?)",
            [(job_id, i, p) for i, p in enumerate(pages)],
        )
        self._db.execute("COMMIT")
        self._wake.set()
        job = self.get(job_id)
        assert job is not None
        return job

    def cancel(self, job_id: str) -> None:
        now = time.time()
        self._db.execute(
            f"UPDATE steps SET state = 'cancelled', finished = ? "
            f"WHERE job = ? AND state IN {ACTIVE_SQL}",
            (now, job_id),
        )
        self._db.execute(
            f"UPDATE jobs SET state = 'cancelled', finished = ? "
            f"WHERE id = ? AND state IN {ACTIVE_SQL}",
            (now, job_id),
        )
        for (job, _), task in list(self._running.items()):
            if job == job_id:
                task.cancel()

    def _with_steps(self, job: dict[str, Any]) -> dict[str, Any]:
        steps = []
        for r in self._db.execute(STEP_LIST, (job["id"],)):
            phase, chars = self._progress.get((job["id"], r["position"]), (None, 0))
            steps.append({**dict(r), "phase": phase, "chars": chars})
        return {**job, "thinking": bool(job["thinking"]), "steps": steps}

    async def _work(self) -> None:
        while True:
            self._wake.clear()
            while claimed := self._claim():
                await self._run(*claimed)
            await self._wake.wait()

    def _claim(self) -> tuple[str, int, int] | None:
        now = time.time()
        row = self._db.execute(CLAIM, (now,)).fetchone()
        if not row:
            return None
        self._db.execute(
            "UPDATE jobs SET state = 'running', started = ? WHERE id = ? AND state = 'queued'",
            (now, row["job"]),
        )
        return row["job"], row["position"], row["page"]

    async def _run(self, job_id: str, position: int, page: int) -> None:
        key = (job_id, position)
        task = asyncio.create_task(self._attempt(key, page))
        self._running[key] = task
        try:
            await asyncio.wait({task})
        finally:
            self._running.pop(key, None)
            self._progress.pop(key, None)
        if not task.cancelled():
            self._end(key, page, task.result())

    async def _attempt(self, key: StepKey, page: int) -> dict[str, Any] | None:
        job = self.get(key[0])
        assert job is not None
        options = job_options(job)
        path = self._store.page_path(page)
        for attempt in range(1, self._attempts + 1):
            self._update_step(key, attempts=attempt)
            context = self._store.context_for(page)
            try:
                async with asyncio.timeout(self._step_timeout):
                    return await self._translate(path, options, context, self._progress_for(key))
            except RETRYABLE as e:
                self._update_step(key, error=self._describe(e))
                if attempt < self._attempts:
                    await asyncio.sleep(self._backoff * 2 ** (attempt - 1))
            except Exception as e:  # noqa: BLE001
                self._update_step(key, error=self._describe(e))
                return None
        return None

    def _describe(self, e: BaseException) -> str:
        if isinstance(e, TimeoutError):
            return f"no answer within {self._step_timeout:.0f}s"
        return f"{type(e).__name__}: {e}"

    def _progress_for(self, key: StepKey) -> Progress:
        def on_progress(phase: str, chars: int) -> None:
            self._progress[key] = (phase, chars)

        return on_progress

    def _update_step(self, key: StepKey, **fields: Any) -> None:
        assignments = ", ".join(f"{k} = ?" for k in fields)
        self._db.execute(
            f"UPDATE steps SET {assignments} WHERE job = ? AND position = ? AND state = 'running'",
            (*fields.values(), *key),
        )

    def _end(self, key: StepKey, page: int, result: dict[str, Any] | None) -> None:
        now = time.time()
        if result is None:
            self._update_step(key, state="failed", finished=now)
        else:
            translation = self._store.add_translation(page, result)
            usage = result.get("usage") or {}
            self._update_step(
                key,
                state="done",
                finished=now,
                error=None,
                translation=translation,
                tokens=usage.get("total_tokens"),
            )
        self._db.execute(FINISH_JOB, (now, key[0]))
