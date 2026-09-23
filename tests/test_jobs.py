import asyncio
import sqlite3
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest

from panelogue.detect import BadOutput, Progress
from panelogue.jobs import ACTIVE, Duplicate, JobQueue

Behaviour = Callable[[str, int], Awaitable[None]]
Job = dict[str, Any]
MakeQueue = Callable[..., Awaitable[JobQueue]]
OPTIONS = {"model": "m", "thinking": False, "lang": "English"}
DEFAULTS: dict[str, Any] = {"concurrency": 2, "attempts": 3, "step_timeout": 0.2, "backoff": 0}


async def ok(page: str, attempt: int) -> None:
    pass


async def hang(page: str, attempt: int) -> None:
    await asyncio.sleep(60)


async def slow(page: str, attempt: int) -> None:
    await asyncio.sleep(0.05)


class FakeTranslate:
    def __init__(self, behaviour: Behaviour = ok) -> None:
        self.behaviour = behaviour
        self.calls: list[tuple[str, str | None]] = []
        self.attempts: dict[str, int] = {}
        self.in_flight = 0
        self.max_in_flight = 0

    async def __call__(
        self, page: str, options: dict[str, Any], previous: str | None, on_progress: Progress
    ) -> dict[str, Any]:
        self.calls.append((page, previous))
        self.attempts[page] = self.attempts.get(page, 0) + 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            on_progress("writing", 10)
            await self.behaviour(page, self.attempts[page])
        finally:
            self.in_flight -= 1
        return {"bubbles": [{"text": page}], "usage": {"total_tokens": 1}}


@pytest.fixture
def db(tmp_path: Path) -> Path:
    return tmp_path / "jobs.db"


@pytest.fixture
async def make_queue(db: Path) -> AsyncIterator[MakeQueue]:
    queues: list[JobQueue] = []

    async def make(translate: FakeTranslate, **kwargs: Any) -> JobQueue:
        queue = JobQueue(translate, db, **{**DEFAULTS, **kwargs})
        await queue.start()
        queues.append(queue)
        return queue

    yield make
    for queue in queues:
        await queue.stop()


async def wait_for(queue: JobQueue, job_id: str, timeout: float = 5) -> Job:
    async with asyncio.timeout(timeout):
        while True:
            job = queue.get(job_id)
            assert job is not None
            if job["state"] not in ACTIVE:
                return job
            await asyncio.sleep(0.01)


def states(job: Job) -> list[str]:
    return [s["state"] for s in job["steps"]]


async def test_pages_run_in_parallel_within_limit(make_queue: MakeQueue, db: Path) -> None:
    translate = FakeTranslate(slow)
    queue = await make_queue(translate, concurrency=2)
    submitted = queue.submit("volume", "v", ["p1", "p2", "p3", "p4"], OPTIONS)
    job = await wait_for(queue, submitted["id"])
    assert job["state"] == "done"
    assert states(job) == ["done"] * 4
    assert translate.max_in_flight == 2
    assert [s["boxes"] for s in job["steps"]] == [1, 1, 1, 1]
    saved = sqlite3.connect(db).execute("SELECT state FROM jobs WHERE id = ?", (job["id"],))
    assert saved.fetchone() == ("done",)


async def test_previous_page_is_passed_as_context(make_queue: MakeQueue) -> None:
    translate = FakeTranslate()
    queue = await make_queue(translate)
    await wait_for(queue, queue.submit("volume", "v", ["p1", "p2", "p3"], OPTIONS)["id"])
    assert sorted(translate.calls) == [("p1", None), ("p2", "p1"), ("p3", "p2")]


async def test_bad_output_is_retried(make_queue: MakeQueue) -> None:
    async def flaky(page: str, attempt: int) -> None:
        if attempt < 3:
            raise BadOutput("garbage")

    queue = await make_queue(FakeTranslate(flaky))
    job = await wait_for(queue, queue.submit("page", "p1", ["p1"], OPTIONS)["id"])
    assert job["state"] == "done"
    assert job["steps"][0]["attempts"] == 3
    assert job["steps"][0]["error"] is None


async def test_hung_call_times_out_then_fails(make_queue: MakeQueue) -> None:
    queue = await make_queue(FakeTranslate(hang), attempts=2, step_timeout=0.05)
    job = await wait_for(queue, queue.submit("page", "p1", ["p1"], OPTIONS)["id"])
    assert job["state"] == "failed"
    assert job["steps"][0]["state"] == "failed"
    assert job["steps"][0]["attempts"] == 2
    assert job["steps"][0]["error"] == "no answer within 0s"


async def test_unexpected_error_fails_without_retry(make_queue: MakeQueue) -> None:
    async def boom(page: str, attempt: int) -> None:
        raise KeyError("bubbles")

    translate = FakeTranslate(boom)
    queue = await make_queue(translate)
    job = await wait_for(queue, queue.submit("volume", "v", ["p1", "p2"], OPTIONS)["id"])
    assert job["state"] == "failed"
    assert translate.attempts == {"p1": 1, "p2": 1}
    assert job["steps"][0]["error"] == "KeyError: 'bubbles'"


async def test_cancel_stops_running_and_queued_steps(make_queue: MakeQueue) -> None:
    translate = FakeTranslate(hang)
    queue = await make_queue(translate, concurrency=1)
    job_id = queue.submit("volume", "v", ["p1", "p2"], OPTIONS)["id"]
    await asyncio.sleep(0.02)
    assert states(queue.get(job_id) or {}) == ["running", "queued"]
    queue.cancel(job_id)
    job = await wait_for(queue, job_id)
    assert job["state"] == "cancelled"
    assert states(job) == ["cancelled", "cancelled"]
    await asyncio.sleep(0.02)
    assert translate.in_flight == 0


async def test_workers_survive_a_cancel(make_queue: MakeQueue) -> None:
    async def hang_p1(page: str, attempt: int) -> None:
        if page == "p1":
            await hang(page, attempt)

    queue = await make_queue(FakeTranslate(hang_p1), concurrency=1)
    first = queue.submit("page", "p1", ["p1"], OPTIONS)["id"]
    await asyncio.sleep(0.02)
    queue.cancel(first)
    job = await wait_for(queue, queue.submit("page", "p2", ["p2"], OPTIONS)["id"])
    assert job["state"] == "done"


async def test_retry_resubmits_only_unfinished_pages(make_queue: MakeQueue) -> None:
    async def fail_p2(page: str, attempt: int) -> None:
        if page == "p2":
            raise BadOutput("garbage")

    translate = FakeTranslate(fail_p2)
    queue = await make_queue(translate)
    job = await wait_for(queue, queue.submit("volume", "v", ["p1", "p2", "p3"], OPTIONS)["id"])
    assert states(job) == ["done", "failed", "done"]
    translate.behaviour = ok
    unfinished = [s["page"] for s in job["steps"] if s["state"] != "done"]
    again = await wait_for(queue, queue.submit("volume", "v", unfinished, OPTIONS)["id"])
    assert [s["page"] for s in again["steps"]] == ["p2"]
    assert again["state"] == "done"


async def test_single_pages_go_before_queued_volume_pages(make_queue: MakeQueue) -> None:
    async def brief(page: str, attempt: int) -> None:
        await asyncio.sleep(0.02)

    translate = FakeTranslate(brief)
    queue = await make_queue(translate, concurrency=1)
    volume = queue.submit("volume", "v", ["v1", "v2", "v3"], OPTIONS)["id"]
    await asyncio.sleep(0.005)
    page = queue.submit("page", "single", ["single"], OPTIONS)["id"]
    await wait_for(queue, page)
    await wait_for(queue, volume)
    assert [p for p, _ in translate.calls] == ["v1", "single", "v2", "v3"]


async def test_restart_resumes_unfinished_jobs(make_queue: MakeQueue) -> None:
    first = await make_queue(FakeTranslate(hang))
    job_id = first.submit("volume", "v", ["p1", "p2", "p3"], OPTIONS)["id"]
    await asyncio.sleep(0.02)
    assert states(first.get(job_id) or {}) == ["running", "running", "queued"]
    await first.stop()

    translate = FakeTranslate()
    second = await make_queue(translate)
    job = await wait_for(second, job_id)
    assert job["state"] == "done"
    assert states(job) == ["done", "done", "done"]
    assert sorted(translate.calls) == [("p1", None), ("p2", "p1"), ("p3", "p2")]


async def test_progress_shows_up_on_running_steps(make_queue: MakeQueue) -> None:
    queue = await make_queue(FakeTranslate(hang))
    job_id = queue.submit("page", "p1", ["p1"], OPTIONS)["id"]
    await asyncio.sleep(0.02)
    [job] = queue.list_jobs()
    assert job["id"] == job_id
    assert job["steps"][0]["phase"] == "writing"
    assert job["steps"][0]["chars"] == 10


async def test_duplicate_submit_is_rejected_until_done(make_queue: MakeQueue) -> None:
    queue = await make_queue(FakeTranslate(slow))
    job = queue.submit("page", "p1", ["p1"], {**OPTIONS, "thinking": True})
    with pytest.raises(Duplicate, match="m, thinking on, English is already queued for this page"):
        queue.submit("page", "p1", ["p1"], {**OPTIONS, "thinking": True})
    queue.submit("page", "p1", ["p1"], OPTIONS)
    await wait_for(queue, job["id"])
    queue.submit("page", "p1", ["p1"], {**OPTIONS, "thinking": True})
