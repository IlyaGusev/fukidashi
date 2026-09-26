import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from fukidashi import store
from fukidashi.detect import list_vision_models, read_source
from fukidashi.jobs import ACTIVE, Duplicate, JobQueue, job_options
from fukidashi.settings import settings

STATIC = Path(__file__).parent / "static"
INDEX = (STATIC / "index.html").read_text()
store.ensure_dirs()
queue = JobQueue(
    concurrency=settings.workers,
    attempts=settings.attempts,
    step_timeout=settings.step_timeout,
    volume_pages_in_order=settings.volume_memory,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await queue.start()
    yield
    await queue.stop()


app = FastAPI(lifespan=lifespan)
app.mount("/pages/files", StaticFiles(directory=store.PAGES), name="pages")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.exception_handler(Duplicate)
async def duplicate_job(request: Request, exc: Duplicate) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=409)


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


def find_job(job_id: str) -> dict[str, Any]:
    job = queue.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    return job


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX


@app.get("/models")
async def models() -> dict[str, Any]:
    return {"models": await list_vision_models(), "default": settings.model, "lang": settings.lang}


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


@app.get("/pages/{page}/rendered")
async def rendered(page: str) -> FileResponse:
    path = await run_in_threadpool(store.render_page, page_name(page))
    if path is None:
        raise HTTPException(404, "no cached result")
    return FileResponse(path, headers={"Cache-Control": "no-cache"})


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


@app.get("/volumes/{name}/memory")
async def volume_memory(
    name: str, model: str = settings.model, lang: str = settings.lang
) -> dict[str, Any]:
    vol = load_volume(name)
    memory = store.volume_memory(vol["name"], model, lang)
    return {"memory": memory.dump() if memory else None}


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
    return {"jobs": queue.list_jobs()}


@app.post("/jobs")
async def create_job(
    kind: str = Form(...),
    name: str = Form(...),
    model: str = Form(settings.model),
    thinking: bool = Form(False),
    lang: str = Form(settings.lang),
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
    return queue.submit(kind, name, pages, {"model": model, "thinking": thinking, "lang": lang})


@app.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: str) -> dict[str, Any]:
    find_job(job_id)
    queue.cancel(job_id)
    return find_job(job_id)


@app.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str) -> dict[str, Any]:
    job = find_job(job_id)
    pages = [s["page"] for s in job["steps"] if s["state"] != "done"]
    if job["state"] in ACTIVE or not pages:
        raise HTTPException(400, "nothing to retry")
    return queue.submit(job["kind"], job["name"], pages, job_options(job))
