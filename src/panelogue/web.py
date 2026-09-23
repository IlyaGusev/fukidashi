import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from panelogue import store
from panelogue.detect import LANG, MODEL, list_vision_models, read_source
from panelogue.jobs import Job, JobQueue

load_dotenv()
INDEX = (Path(__file__).parent / "static" / "index.html").read_text()
store.ensure_dirs()
queue = JobQueue(
    concurrency=int(os.environ.get("PANELOGUE_WORKERS", "2")),
    attempts=int(os.environ.get("PANELOGUE_ATTEMPTS", "3")),
    step_timeout=float(os.environ.get("PANELOGUE_STEP_TIMEOUT", "600")),
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await queue.start()
    yield
    await queue.stop()


app = FastAPI(lifespan=lifespan)
app.mount("/pages/files", StaticFiles(directory=store.PAGES), name="pages")
SAMPLE_URL = "https://raw.githubusercontent.com/mantra-inc/open-mantra-dataset/main/images/{book}/ja/{page:03d}.jpg"
SAMPLES = {
    "tojime_no_siora": 46,
    "balloon_dream": 38,
    "tencho_isoro": 40,
    "boureisougi": 36,
    "rasetugari": 54,
}


def page_name(page: str) -> str:
    name = Path(page).name
    if not store.page_exists(name):
        raise HTTPException(404, "unknown page")
    return name


def load_volume(name: str) -> dict[str, Any]:
    vol = store.load_volume(name)
    if vol is None:
        raise HTTPException(404, "unknown volume")
    return vol


def find_job(job_id: str) -> Job:
    job = queue.jobs.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    return job


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX


@app.get("/models")
async def models() -> dict[str, Any]:
    return {"models": await list_vision_models(), "default": MODEL, "lang": LANG}


@app.get("/pages")
async def pages() -> dict[str, Any]:
    return {"pages": store.list_pages()}


@app.post("/pages")
async def upload(image: UploadFile = File(...)) -> dict[str, str]:
    return {"page": store.save_page(await image.read(), image.filename, image.content_type)}


@app.get("/results/{page}")
async def result(page: str) -> JSONResponse:
    found = store.load_result(Path(page).name)
    if found is None:
        raise HTTPException(404, "no cached result")
    return JSONResponse(found)


@app.get("/volumes")
async def volumes() -> dict[str, Any]:
    return {"volumes": store.list_volumes()}


@app.post("/volumes")
async def create_volume(name: str = Form(...)) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise HTTPException(400, "empty name")
    if not store.volume_path(name).exists():
        store.save_volume(name, [])
    return load_volume(name)


@app.get("/volumes/{name}")
async def volume(name: str) -> dict[str, Any]:
    return load_volume(name)


@app.get("/samples")
async def samples() -> dict[str, Any]:
    return {"samples": list(SAMPLES)}


@app.post("/samples/{book}")
async def import_sample(book: str) -> dict[str, Any]:
    if book not in SAMPLES:
        raise HTTPException(404, "unknown sample")
    name = f"OpenMantra {book}"
    if not store.volume_path(name).exists():
        urls = [SAMPLE_URL.format(book=book, page=i) for i in range(SAMPLES[book])]
        downloads = await asyncio.gather(*(run_in_threadpool(read_source, u) for u in urls))
        pages = [
            store.save_page(data, f"{book}_{i:03d}.jpg", mime)
            for i, (data, mime) in enumerate(downloads)
        ]
        store.save_volume(name, pages)
    return load_volume(name)


@app.post("/volumes/{name}/pages")
async def add_pages(name: str, images: list[UploadFile] = File(...)) -> dict[str, Any]:
    vol = load_volume(name)
    existing = [p["name"] for p in vol["pages"]]
    uploads = sorted(images, key=lambda f: f.filename or "")
    for f in uploads:
        page = store.save_page(await f.read(), f.filename, f.content_type)
        if page not in existing:
            existing.append(page)
    store.save_volume(name, existing)
    return load_volume(name)


@app.get("/jobs")
async def jobs() -> dict[str, Any]:
    return {"jobs": [j.to_dict() for j in queue.jobs.values()]}


@app.post("/jobs")
async def create_job(
    kind: str = Form(...),
    name: str = Form(...),
    model: str = Form(MODEL),
    thinking: bool = Form(False),
    lang: str = Form(LANG),
) -> dict[str, Any]:
    if kind == "page":
        name = page_name(name)
        pages = [name]
    elif kind == "volume":
        vol = load_volume(name)
        name = vol["name"]
        pages = [p["name"] for p in vol["pages"]]
        if not pages:
            raise HTTPException(400, "volume has no pages")
    else:
        raise HTTPException(400, "kind must be page or volume")
    if queue.active_for(kind, name):
        raise HTTPException(409, "already queued")
    options = {"model": model, "thinking": thinking, "lang": lang}
    return queue.submit(kind, name, pages, options).to_dict()


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> dict[str, Any]:
    job = find_job(job_id)
    queue.cancel(job)
    return job.to_dict()


@app.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str) -> dict[str, Any]:
    job = find_job(job_id)
    if job.active or not job.unfinished_pages:
        raise HTTPException(400, "nothing to retry")
    if queue.active_for(job.kind, job.name):
        raise HTTPException(409, "already queued")
    return queue.retry(job).to_dict()


@app.get("/events")
async def events() -> StreamingResponse:
    async def stream() -> AsyncIterator[str]:
        async for event in queue.subscribe():
            yield f"data: {json.dumps(event)}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(stream(), media_type="text/event-stream", headers=headers)
