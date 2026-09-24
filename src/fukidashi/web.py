import asyncio
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

from fukidashi.detect import list_vision_models, read_source
from fukidashi.jobs import ACTIVE, Duplicate, JobQueue, job_options
from fukidashi.settings import settings
from fukidashi.store import Store

STATIC = Path(__file__).parent / "static"
INDEX = (STATIC / "index.html").read_text()
store = Store(settings.data_dir)
queue = JobQueue(
    store,
    concurrency=settings.workers,
    attempts=settings.attempts,
    step_timeout=settings.step_timeout,
)
SAMPLE_URL = "https://raw.githubusercontent.com/mantra-inc/open-mantra-dataset/main/images/{book}/ja/{page:03d}.jpg"
SAMPLES = {
    "tojime_no_siora": 46,
    "balloon_dream": 38,
    "tencho_isoro": 40,
    "boureisougi": 36,
    "rasetugari": 54,
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await queue.start()
    yield
    await queue.stop()
    store.close()


app = FastAPI(lifespan=lifespan)
app.mount("/pages/files", StaticFiles(directory=store.pages_dir), name="pages")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.exception_handler(Duplicate)
async def duplicate_job(request: Request, exc: Duplicate) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=409)


@app.exception_handler(sqlite3.IntegrityError)
async def integrity_error(request: Request, exc: sqlite3.IntegrityError) -> JSONResponse:
    return JSONResponse({"detail": "a volume with this title already exists"}, status_code=409)


class VolumeIn(BaseModel):
    title: str


class OrderIn(BaseModel):
    pages: list[int]


class CurrentIn(BaseModel):
    translation: int


class JobIn(BaseModel):
    volume: int
    pages: list[int] | None = None
    model: str = settings.model
    thinking: bool = False
    lang: str = settings.lang


def find_volume(volume: int) -> dict[str, Any]:
    found = store.get_volume(volume)
    if found is None:
        raise HTTPException(404, "unknown volume")
    return found


def find_page(page: int) -> dict[str, Any]:
    found = store.get_page(page)
    if found is None:
        raise HTTPException(404, "unknown page")
    return found


def find_job(job_id: str) -> dict[str, Any]:
    job = queue.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    return job


def clean_title(title: str) -> str:
    title = title.strip()
    if not title:
        raise HTTPException(400, "empty title")
    return title


def ensure_idle(pages: list[int]) -> None:
    if queue.busy(pages):
        raise HTTPException(409, "a job is still working on these pages")


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX


@app.get("/models")
async def models() -> dict[str, Any]:
    return {"models": await list_vision_models(), "default": settings.model, "lang": settings.lang}


@app.get("/volumes")
async def volumes() -> dict[str, Any]:
    return {"volumes": store.list_volumes()}


@app.post("/volumes")
async def create_volume(body: VolumeIn) -> dict[str, Any]:
    return store.create_volume(clean_title(body.title))


@app.get("/volumes/{volume}")
async def volume(volume: int) -> dict[str, Any]:
    return find_volume(volume)


@app.post("/volumes/{volume}/title")
async def rename_volume(volume: int, body: VolumeIn) -> dict[str, Any]:
    find_volume(volume)
    store.rename_volume(volume, clean_title(body.title))
    return find_volume(volume)


@app.delete("/volumes/{volume}")
async def delete_volume(volume: int) -> dict[str, Any]:
    find_volume(volume)
    ensure_idle(store.volume_pages(volume))
    store.delete_volume(volume)
    return {"volumes": store.list_volumes()}


@app.post("/volumes/{volume}/pages")
async def add_pages(volume: int, images: list[UploadFile] = File(...)) -> dict[str, Any]:
    find_volume(volume)
    uploads = sorted(images, key=lambda f: f.filename or "")
    store.add_pages(volume, [(await f.read(), f.filename, f.content_type) for f in uploads])
    return find_volume(volume)


@app.post("/volumes/{volume}/order")
async def reorder_pages(volume: int, body: OrderIn) -> dict[str, Any]:
    if sorted(body.pages) != sorted(store.volume_pages(volume)):
        raise HTTPException(400, "order must list every page of the volume once")
    store.reorder_pages(volume, body.pages)
    return find_volume(volume)


@app.get("/pages/{page}")
async def page(page: int) -> dict[str, Any]:
    return find_page(page)


@app.delete("/pages/{page}")
async def remove_page(page: int) -> dict[str, Any]:
    found = find_page(page)
    ensure_idle([page])
    store.remove_page(page)
    return find_volume(found["volume"])


@app.post("/pages/{page}/current")
async def set_current(page: int, body: CurrentIn) -> dict[str, Any]:
    if not store.set_current(page, body.translation):
        raise HTTPException(404, "unknown page or translation")
    return find_page(page)


@app.get("/translations/{translation}")
async def translation(translation: int) -> JSONResponse:
    found = store.get_translation(translation)
    if found is None:
        raise HTTPException(404, "unknown translation")
    return JSONResponse(found)


@app.get("/translations/{translation}/rendered")
async def rendered(translation: int) -> FileResponse:
    path = await run_in_threadpool(store.render, translation)
    if path is None:
        raise HTTPException(404, "unknown translation")
    return FileResponse(path, headers={"Cache-Control": "no-cache"})


@app.get("/samples")
async def samples() -> dict[str, Any]:
    return {"samples": list(SAMPLES)}


@app.post("/samples/{book}")
async def import_sample(book: str) -> dict[str, Any]:
    if book not in SAMPLES:
        raise HTTPException(404, "unknown sample")
    title = f"OpenMantra {book}"
    if existing := store.volume_by_title(title):
        return existing
    urls = [SAMPLE_URL.format(book=book, page=i) for i in range(SAMPLES[book])]
    downloads = await asyncio.gather(*(run_in_threadpool(read_source, u) for u in urls))
    created = store.create_volume(title)
    store.add_pages(
        created["id"],
        [(data, f"{book}_{i:03d}.jpg", mime) for i, (data, mime) in enumerate(downloads)],
    )
    return find_volume(created["id"])


@app.get("/jobs")
async def jobs() -> dict[str, Any]:
    return {"jobs": queue.list_jobs()}


@app.post("/jobs")
async def create_job(body: JobIn) -> dict[str, Any]:
    find_volume(body.volume)
    all_pages = store.volume_pages(body.volume)
    pages = all_pages if body.pages is None else [p for p in body.pages if p in all_pages]
    if not pages:
        raise HTTPException(400, "no pages to translate")
    options = {"model": body.model, "thinking": body.thinking, "lang": body.lang}
    return queue.submit(body.volume, pages, options)


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> dict[str, Any]:
    find_job(job_id)
    queue.cancel(job_id)
    return find_job(job_id)


@app.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str) -> dict[str, Any]:
    job = find_job(job_id)
    pages = [s["page"] for s in job["steps"] if s["state"] != "done" and s["page"] is not None]
    if job["state"] in ACTIVE or not pages:
        raise HTTPException(400, "nothing to retry")
    return queue.submit(job["volume"], pages, job_options(job))
