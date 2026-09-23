import hashlib
import json
import mimetypes
import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from panelogue.detect import LANG, MODEL, list_vision_models
from panelogue.jobs import PAGES, RESULTS, JobQueue

load_dotenv()
INDEX = (Path(__file__).parent / "static" / "index.html").read_text()
VOLUMES = Path("data/volumes")
for d in (PAGES, RESULTS, VOLUMES):
    d.mkdir(parents=True, exist_ok=True)
queue = JobQueue(workers=int(os.environ.get("PANELOGUE_WORKERS", "2")))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await queue.start()
    yield
    await queue.stop()


app = FastAPI(lifespan=lifespan)
app.mount("/pages/files", StaticFiles(directory=PAGES), name="pages")


def safe(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name.strip())[:60] or "untitled"


def save_page(data: bytes, filename: str | None, content_type: str | None) -> str:
    ext = Path(filename or "").suffix or mimetypes.guess_extension(content_type or "") or ".png"
    name = f"{hashlib.sha1(data).hexdigest()[:12]}__{safe(Path(filename or 'page').stem)}{ext}"
    path = PAGES / name
    if not path.exists():
        path.write_bytes(data)
    return name


def page_name(page: str) -> str:
    name = Path(page).name
    if not (PAGES / name).is_file():
        raise HTTPException(404, "unknown page")
    return name


def page_info(name: str) -> dict[str, Any]:
    return {"name": name, "cached": (RESULTS / f"{name}.json").exists()}


def load_volume(name: str) -> dict[str, Any]:
    path = VOLUMES / f"{safe(name)}.json"
    if not path.is_file():
        raise HTTPException(404, "unknown volume")
    vol: dict[str, Any] = json.loads(path.read_text())
    vol["pages"] = [page_info(p) for p in vol["pages"]]
    return vol


def save_volume(name: str, pages: list[str]) -> None:
    (VOLUMES / f"{safe(name)}.json").write_text(json.dumps({"name": name, "pages": pages}))


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return INDEX


@app.get("/models")
async def models() -> dict[str, Any]:
    return {"models": await list_vision_models(), "default": MODEL, "lang": LANG}


@app.get("/pages")
async def pages() -> dict[str, Any]:
    files = sorted(PAGES.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"pages": [page_info(p.name) for p in files]}


@app.post("/pages")
async def upload(image: UploadFile = File(...)) -> dict[str, str]:
    return {"page": save_page(await image.read(), image.filename, image.content_type)}


@app.get("/results/{page}")
async def result(page: str) -> JSONResponse:
    path = RESULTS / f"{Path(page).name}.json"
    if not path.is_file():
        raise HTTPException(404, "no cached result")
    return JSONResponse(json.loads(path.read_text()))


@app.get("/volumes")
async def volumes() -> dict[str, Any]:
    names = sorted(json.loads(p.read_text())["name"] for p in VOLUMES.glob("*.json"))
    return {"volumes": names}


@app.post("/volumes")
async def create_volume(name: str = Form(...)) -> dict[str, Any]:
    name = name.strip()
    if not name:
        raise HTTPException(400, "empty name")
    if not (VOLUMES / f"{safe(name)}.json").exists():
        save_volume(name, [])
    return load_volume(name)


@app.get("/volumes/{name}")
async def volume(name: str) -> dict[str, Any]:
    return load_volume(name)


@app.post("/volumes/{name}/pages")
async def add_pages(name: str, images: list[UploadFile] = File(...)) -> dict[str, Any]:
    vol = load_volume(name)
    existing = [p["name"] for p in vol["pages"]]
    uploads = sorted(images, key=lambda f: f.filename or "")
    for f in uploads:
        page = save_page(await f.read(), f.filename, f.content_type)
        if page not in existing:
            existing.append(page)
    save_volume(name, existing)
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
    job = queue.jobs.get(job_id)
    if not job:
        raise HTTPException(404, "unknown job")
    queue.cancel(job)
    return job.to_dict()


@app.get("/events")
async def events() -> StreamingResponse:
    async def stream() -> AsyncIterator[str]:
        async for event in queue.subscribe():
            yield f"data: {json.dumps(event)}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(stream(), media_type="text/event-stream", headers=headers)
