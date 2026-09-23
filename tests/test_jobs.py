import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest

from fukidashi import jobs
from fukidashi.detect import BadOutput, Progress
from fukidashi.jobs import Job, JobQueue, Step

Behaviour = Callable[[str, int], Awaitable[None]]
OPTIONS = {"model": "m", "thinking": False, "lang": "English"}


async def ok(page: str, attempt: int) -> None:
    pass


class FakeTranslate:
    def __init__(self, behaviour: Behaviour = ok) -> None:
        self.behaviour = behaviour
        self.calls: list[tuple[str, str | None]] = []
        self.volumes: set[str | None] = set()
        self.attempts: dict[str, int] = {}
        self.in_flight = 0
        self.max_in_flight = 0

    async def __call__(
        self,
        page: str,
        options: dict[str, Any],
        previous: str | None,
        volume: str | None,
        on_progress: Progress,
    ) -> dict[str, Any]:
        self.calls.append((page, previous))
        self.volumes.add(volume)
        self.attempts[page] = self.attempts.get(page, 0) + 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            on_progress("writing", 10)
            await self.behaviour(page, self.attempts[page])
        finally:
            self.in_flight -= 1
        return {"bubbles": [{"text": page}], "usage": {"total_tokens": 1}}


@pytest.fixture(autouse=True)
def jobs_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(jobs, "JOBS", tmp_path)
    return tmp_path


def make_queue(translate: FakeTranslate, **kwargs: Any) -> JobQueue:
    defaults: dict[str, Any] = {"concurrency": 2, "attempts": 3, "step_timeout": 0.2, "backoff": 0}
    return JobQueue(translate, **{**defaults, **kwargs})


async def wait_for(job: Job, timeout: float = 5) -> Job:
    async with asyncio.timeout(timeout):
        while job.active:
            await asyncio.sleep(0.01)
    return job


def states(job: Job) -> list[str]:
    return [s.state for s in job.steps]


async def test_pages_run_in_parallel_within_limit(jobs_dir: Path) -> None:
    async def slow(page: str, attempt: int) -> None:
        await asyncio.sleep(0.05)

    translate = FakeTranslate(slow)
    queue = make_queue(translate, concurrency=2)
    await queue.start()
    job = await wait_for(queue.submit("volume", "v", ["p1", "p2", "p3", "p4"], OPTIONS))
    assert job.state == "done"
    assert states(job) == ["done"] * 4
    assert translate.max_in_flight == 2
    assert [s.boxes for s in job.steps] == [1, 1, 1, 1]
    assert json.loads((jobs_dir / f"{job.id}.json").read_text())["state"] == "done"


async def test_previous_page_is_passed_as_context() -> None:
    translate = FakeTranslate()
    queue = make_queue(translate)
    await queue.start()
    await wait_for(queue.submit("volume", "v", ["p1", "p2", "p3"], OPTIONS))
    assert sorted(translate.calls) == [("p1", None), ("p2", "p1"), ("p3", "p2")]
    assert translate.volumes == {"v"}


async def test_page_jobs_have_no_volume() -> None:
    translate = FakeTranslate()
    queue = make_queue(translate)
    await queue.start()
    await wait_for(queue.submit("page", "p1", ["p1"], OPTIONS))
    assert translate.volumes == {None}


async def test_bad_output_is_retried() -> None:
    async def flaky(page: str, attempt: int) -> None:
        if attempt < 3:
            raise BadOutput("garbage")

    translate = FakeTranslate(flaky)
    queue = make_queue(translate)
    await queue.start()
    job = await wait_for(queue.submit("page", "p1", ["p1"], OPTIONS))
    assert job.state == "done"
    assert job.steps[0].attempts == 3
    assert job.steps[0].error is None


async def test_hung_call_times_out_then_fails() -> None:
    async def hang(page: str, attempt: int) -> None:
        await asyncio.sleep(60)

    translate = FakeTranslate(hang)
    queue = make_queue(translate, attempts=2, step_timeout=0.05)
    await queue.start()
    job = await wait_for(queue.submit("page", "p1", ["p1"], OPTIONS))
    assert job.state == "failed"
    assert job.steps[0].state == "failed"
    assert job.steps[0].attempts == 2
    assert job.steps[0].error == "no answer within 0s"


async def test_unexpected_error_fails_without_retry() -> None:
    async def boom(page: str, attempt: int) -> None:
        raise KeyError("bubbles")

    translate = FakeTranslate(boom)
    queue = make_queue(translate)
    await queue.start()
    job = await wait_for(queue.submit("volume", "v", ["p1", "p2"], OPTIONS))
    assert job.state == "failed"
    assert translate.attempts == {"p1": 1, "p2": 1}
    assert job.steps[0].error == "KeyError: 'bubbles'"


async def test_cancel_stops_running_and_queued_steps() -> None:
    async def slow(page: str, attempt: int) -> None:
        await asyncio.sleep(60)

    translate = FakeTranslate(slow)
    queue = make_queue(translate, concurrency=1)
    await queue.start()
    job = queue.submit("volume", "v", ["p1", "p2"], OPTIONS)
    await asyncio.sleep(0.02)
    assert states(job) == ["running", "queued"]
    queue.cancel(job)
    await wait_for(job)
    assert job.state == "cancelled"
    assert states(job) == ["cancelled", "cancelled"]
    assert translate.in_flight == 0


async def test_retry_resubmits_only_unfinished_pages() -> None:
    async def fail_p2(page: str, attempt: int) -> None:
        if page == "p2":
            raise BadOutput("garbage")

    translate = FakeTranslate(fail_p2)
    queue = make_queue(translate)
    await queue.start()
    job = await wait_for(queue.submit("volume", "v", ["p1", "p2", "p3"], OPTIONS))
    assert states(job) == ["done", "failed", "done"]
    translate.behaviour = ok
    again = await wait_for(queue.retry(job))
    assert [s.page for s in again.steps] == ["p2"]
    assert again.state == "done"


async def test_restart_resumes_unfinished_jobs(jobs_dir: Path) -> None:
    interrupted = Job(
        "abc",
        "volume",
        "v",
        OPTIONS,
        [Step("p1", state="done", boxes=3), Step("p2", state="running"), Step("p3")],
        state="running",
    )
    (jobs_dir / "abc.json").write_text(json.dumps(interrupted.to_dict()))
    translate = FakeTranslate()
    queue = make_queue(translate)
    await queue.start()
    job = await wait_for(queue.jobs["abc"])
    assert job.state == "done"
    assert states(job) == ["done", "done", "done"]
    assert sorted(translate.calls) == [("p2", "p1"), ("p3", "p2")]


async def test_stop_keeps_jobs_resumable(jobs_dir: Path) -> None:
    async def slow(page: str, attempt: int) -> None:
        await asyncio.sleep(60)

    queue = make_queue(FakeTranslate(slow))
    await queue.start()
    job = queue.submit("page", "p1", ["p1"], OPTIONS)
    await asyncio.sleep(0.02)
    await queue.stop()
    saved = json.loads((jobs_dir / f"{job.id}.json").read_text())
    assert saved["state"] == "running"
    assert saved["steps"][0]["state"] == "running"


async def test_events_carry_snapshot_progress_and_job_updates() -> None:
    queue = make_queue(FakeTranslate())
    await queue.start()
    events = queue.subscribe()
    snapshot = await anext(events)
    assert snapshot["type"] == "snapshot"
    assert snapshot["concurrency"] == 2
    job = queue.submit("page", "p1", ["p1"], OPTIONS)
    seen: list[dict[str, Any]] = []
    async with asyncio.timeout(5):
        while not (seen and seen[-1]["type"] == "job" and seen[-1]["job"]["state"] == "done"):
            seen.append(await anext(events))
    types = [e["type"] for e in seen]
    assert types[:2] == ["job", "job"]
    assert {"type": "progress", "id": job.id, "step": 0, "phase": "writing", "chars": 10} in seen
    assert seen[-1]["job"]["steps"][0]["boxes"] == 1


async def test_active_for_matches_only_identical_options() -> None:
    translate = FakeTranslate(lambda page, attempt: asyncio.sleep(0.05))
    queue = make_queue(translate)
    job = queue.submit("page", "p1", ["p1"], OPTIONS)
    assert queue.active_for("page", "p1", OPTIONS) is job
    assert queue.active_for("page", "p1", {**OPTIONS, "model": "other"}) is None
    await wait_for(job)
    assert queue.active_for("page", "p1", OPTIONS) is None


async def test_duplicate_message_names_the_settings() -> None:
    translate = FakeTranslate(lambda page, attempt: asyncio.sleep(0.05))
    queue = make_queue(translate)
    job = queue.submit("page", "p1", ["p1"], {**OPTIONS, "thinking": True})
    assert job.duplicate_message() == (
        "m, thinking on, English is already queued for this page. "
        "Change a setting to queue another run."
    )
    await wait_for(job)
