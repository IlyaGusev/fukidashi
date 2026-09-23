import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import Any

import pytest

from fukidashi.detect import BadOutput, Progress
from fukidashi.jobs import ACTIVE, Duplicate, JobQueue
from fukidashi.store import Store

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


def label(path: Path) -> str:
    return path.stem.split("__", 1)[1]


class FakeTranslate:
    def __init__(self, behaviour: Behaviour = ok) -> None:
        self.behaviour = behaviour
        self.calls: list[tuple[str, list[str] | None]] = []
        self.attempts: dict[str, int] = {}
        self.in_flight = 0
        self.max_in_flight = 0

    async def __call__(
        self, path: Path, options: dict[str, Any], context: list[str] | None, on_progress: Progress
    ) -> dict[str, Any]:
        page = label(path)
        self.calls.append((page, context))
        self.attempts[page] = self.attempts.get(page, 0) + 1
        self.in_flight += 1
        self.max_in_flight = max(self.max_in_flight, self.in_flight)
        try:
            on_progress("writing", 10)
            await self.behaviour(page, self.attempts[page])
        finally:
            self.in_flight -= 1
        return {
            **OPTIONS,
            "bubbles": [{"text": page}],
            "size": [1, 1],
            "usage": {"total_tokens": 1},
        }


@pytest.fixture
def store(tmp_path: Path) -> Store:
    return Store(tmp_path)


@pytest.fixture
async def make_queue(store: Store) -> AsyncIterator[MakeQueue]:
    queues: list[JobQueue] = []

    async def make(translate: FakeTranslate, **kwargs: Any) -> JobQueue:
        queue = JobQueue(store, translate, **{**DEFAULTS, **kwargs})
        await queue.start()
        queues.append(queue)
        return queue

    yield make
    for queue in queues:
        await queue.stop()


def volume_with(store: Store, *names: str) -> tuple[int, list[int]]:
    volume = store.create_volume(names[0] + "-volume")["id"]
    store.add_pages(volume, [(name.encode(), f"{name}.png", "image/png") for name in names])
    return volume, store.volume_pages(volume)


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


def pages_of(job: Job) -> list[str]:
    return [label(Path(s["file"])) for s in job["steps"]]


async def test_pages_run_in_parallel_within_limit(store: Store, make_queue: MakeQueue) -> None:
    translate = FakeTranslate(slow)
    queue = await make_queue(translate, concurrency=2)
    volume, pages = volume_with(store, "p1", "p2", "p3", "p4")
    job = await wait_for(queue, queue.submit(volume, pages, OPTIONS)["id"])
    assert job["state"] == "done"
    assert states(job) == ["done"] * 4
    assert translate.max_in_flight == 2
    assert [s["tokens"] for s in job["steps"]] == [1, 1, 1, 1]


async def test_done_steps_store_a_translation_and_make_it_current(
    store: Store, make_queue: MakeQueue
) -> None:
    queue = await make_queue(FakeTranslate())
    volume, [page] = volume_with(store, "p1")
    job = await wait_for(queue, queue.submit(volume, [page], OPTIONS)["id"])
    again = await wait_for(queue, queue.submit(volume, [page], OPTIONS)["id"])
    first, second = job["steps"][0]["translation"], again["steps"][0]["translation"]
    found = store.get_page(page)
    assert found is not None
    assert found["current"] == second
    assert [v["id"] for v in found["versions"]] == [second, first]
    assert store.set_current(page, first)
    assert (store.get_page(page) or {})["current"] == first


async def test_previous_page_text_is_passed_as_context(store: Store, make_queue: MakeQueue) -> None:
    translate = FakeTranslate()
    queue = await make_queue(translate, concurrency=1)
    volume, pages = volume_with(store, "p1", "p2", "p3")
    await wait_for(queue, queue.submit(volume, pages, OPTIONS)["id"])
    assert translate.calls == [("p1", None), ("p2", ["p1"]), ("p3", ["p2"])]


async def test_context_comes_from_the_current_version(store: Store, make_queue: MakeQueue) -> None:
    translate = FakeTranslate()
    queue = await make_queue(translate)
    volume, [p1, p2] = volume_with(store, "p1", "p2")
    await wait_for(queue, queue.submit(volume, [p1], OPTIONS)["id"])
    store.set_current(p1, store.add_translation(p1, {**OPTIONS, "bubbles": [{"text": "old"}]}))
    await wait_for(queue, queue.submit(volume, [p2], OPTIONS)["id"])
    assert translate.calls[-1] == ("p2", ["old"])


async def test_bad_output_is_retried(store: Store, make_queue: MakeQueue) -> None:
    async def flaky(page: str, attempt: int) -> None:
        if attempt < 3:
            raise BadOutput("garbage")

    queue = await make_queue(FakeTranslate(flaky))
    volume, pages = volume_with(store, "p1")
    job = await wait_for(queue, queue.submit(volume, pages, OPTIONS)["id"])
    assert job["state"] == "done"
    assert job["steps"][0]["attempts"] == 3
    assert job["steps"][0]["error"] is None


async def test_hung_call_times_out_then_fails(store: Store, make_queue: MakeQueue) -> None:
    queue = await make_queue(FakeTranslate(hang), attempts=2, step_timeout=0.05)
    volume, pages = volume_with(store, "p1")
    job = await wait_for(queue, queue.submit(volume, pages, OPTIONS)["id"])
    assert job["state"] == "failed"
    assert job["steps"][0]["state"] == "failed"
    assert job["steps"][0]["attempts"] == 2
    assert job["steps"][0]["error"] == "no answer within 0s"


async def test_unexpected_error_fails_without_retry(store: Store, make_queue: MakeQueue) -> None:
    async def boom(page: str, attempt: int) -> None:
        raise KeyError("bubbles")

    translate = FakeTranslate(boom)
    queue = await make_queue(translate)
    volume, pages = volume_with(store, "p1", "p2")
    job = await wait_for(queue, queue.submit(volume, pages, OPTIONS)["id"])
    assert job["state"] == "failed"
    assert translate.attempts == {"p1": 1, "p2": 1}
    assert job["steps"][0]["error"] == "KeyError: 'bubbles'"


async def test_cancel_stops_running_and_queued_steps(store: Store, make_queue: MakeQueue) -> None:
    translate = FakeTranslate(hang)
    queue = await make_queue(translate, concurrency=1)
    volume, pages = volume_with(store, "p1", "p2")
    job_id = queue.submit(volume, pages, OPTIONS)["id"]
    await asyncio.sleep(0.02)
    assert states(queue.get(job_id) or {}) == ["running", "queued"]
    queue.cancel(job_id)
    job = await wait_for(queue, job_id)
    assert job["state"] == "cancelled"
    assert states(job) == ["cancelled", "cancelled"]
    await asyncio.sleep(0.02)
    assert translate.in_flight == 0


async def test_workers_survive_a_cancel(store: Store, make_queue: MakeQueue) -> None:
    async def hang_p1(page: str, attempt: int) -> None:
        if page == "p1":
            await hang(page, attempt)

    queue = await make_queue(FakeTranslate(hang_p1), concurrency=1)
    volume, [p1, p2] = volume_with(store, "p1", "p2")
    first = queue.submit(volume, [p1], OPTIONS)["id"]
    await asyncio.sleep(0.02)
    queue.cancel(first)
    job = await wait_for(queue, queue.submit(volume, [p2], OPTIONS)["id"])
    assert job["state"] == "done"


async def test_retry_resubmits_only_unfinished_pages(store: Store, make_queue: MakeQueue) -> None:
    async def fail_p2(page: str, attempt: int) -> None:
        if page == "p2":
            raise BadOutput("garbage")

    translate = FakeTranslate(fail_p2)
    queue = await make_queue(translate)
    volume, pages = volume_with(store, "p1", "p2", "p3")
    job = await wait_for(queue, queue.submit(volume, pages, OPTIONS)["id"])
    assert states(job) == ["done", "failed", "done"]
    translate.behaviour = ok
    unfinished = [s["page"] for s in job["steps"] if s["state"] != "done"]
    again = await wait_for(queue, queue.submit(volume, unfinished, OPTIONS)["id"])
    assert pages_of(again) == ["p2"]
    assert again["state"] == "done"


async def test_single_pages_go_before_queued_volume_pages(
    store: Store, make_queue: MakeQueue
) -> None:
    async def brief(page: str, attempt: int) -> None:
        await asyncio.sleep(0.02)

    translate = FakeTranslate(brief)
    queue = await make_queue(translate, concurrency=1)
    volume, pages = volume_with(store, "v1", "v2", "v3")
    other, [single] = volume_with(store, "single")
    volume_job = queue.submit(volume, pages, OPTIONS)["id"]
    await asyncio.sleep(0.005)
    page_job = queue.submit(other, [single], OPTIONS)["id"]
    await wait_for(queue, page_job)
    await wait_for(queue, volume_job)
    assert [p for p, _ in translate.calls] == ["v1", "single", "v2", "v3"]


async def test_restart_resumes_unfinished_jobs(store: Store, make_queue: MakeQueue) -> None:
    first = await make_queue(FakeTranslate(hang))
    volume, pages = volume_with(store, "p1", "p2", "p3")
    job_id = first.submit(volume, pages, OPTIONS)["id"]
    await asyncio.sleep(0.02)
    assert states(first.get(job_id) or {}) == ["running", "running", "queued"]
    await first.stop()

    translate = FakeTranslate()
    second = await make_queue(translate)
    job = await wait_for(second, job_id)
    assert job["state"] == "done"
    assert states(job) == ["done", "done", "done"]
    assert sorted(p for p, _ in translate.calls) == ["p1", "p2", "p3"]


async def test_progress_shows_up_on_running_steps(store: Store, make_queue: MakeQueue) -> None:
    queue = await make_queue(FakeTranslate(hang))
    volume, pages = volume_with(store, "p1")
    job_id = queue.submit(volume, pages, OPTIONS)["id"]
    await asyncio.sleep(0.02)
    [job] = queue.list_jobs()
    assert job["id"] == job_id
    assert job["title"] == "p1-volume"
    assert job["steps"][0]["phase"] == "writing"
    assert job["steps"][0]["chars"] == 10


async def test_duplicate_submit_is_rejected_until_done(store: Store, make_queue: MakeQueue) -> None:
    queue = await make_queue(FakeTranslate(slow))
    volume, pages = volume_with(store, "p1")
    thinking = {**OPTIONS, "thinking": True}
    job = queue.submit(volume, pages, thinking)
    with pytest.raises(Duplicate, match="m, thinking on, English is already queued"):
        queue.submit(volume, pages, thinking)
    queue.submit(volume, pages, OPTIONS)
    assert queue.busy(pages)
    await wait_for(queue, job["id"])
    queue.submit(volume, pages, thinking)


async def test_removing_a_page_keeps_the_job_history(store: Store, make_queue: MakeQueue) -> None:
    queue = await make_queue(FakeTranslate())
    volume, [p1, p2] = volume_with(store, "p1", "p2")
    job = await wait_for(queue, queue.submit(volume, [p1, p2], OPTIONS)["id"])
    store.remove_page(p1)
    assert store.volume_pages(volume) == [p2]
    assert store.get_translation(job["steps"][0]["translation"]) is None
    found = queue.get(job["id"])
    assert found is not None
    assert [s["page"] for s in found["steps"]] == [None, p2]
    store.delete_volume(volume)
    assert queue.get(job["id"]) is None
