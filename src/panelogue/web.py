import asyncio
import hashlib
import json
import mimetypes
import re
import threading
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from panelogue.detect import LANG, MODEL, detect_bytes, list_vision_models, read_source

load_dotenv()
app = FastAPI()
INDEX = (Path(__file__).parent / "static" / "index.html").read_text()
PAGES = Path("data/pages")
RESULTS = Path("data/results")
VOLUMES = Path("data/volumes")
for d in (PAGES, RESULTS, VOLUMES):
    d.mkdir(parents=True, exist_ok=True)
app.mount("/pages/files", StaticFiles(directory=PAGES), name="pages")
JOBS: dict[str, dict] = {}
SAMPLE_URL = "https://raw.githubusercontent.com/mantra-inc/open-mantra-dataset/main/images/{book}/ja/{page:03d}.jpg"
SAMPLES = {"tojime_no_siora": 46, "balloon_dream": 38, "tencho_isoro": 40, "boureisougi": 36, "rasetugari": 54}


def safe(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name.strip())[:60] or "untitled"


def save_page(data: bytes, filename: str | None, content_type: str | None) -> str:
    ext = Path(filename or "").suffix or mimetypes.guess_extension(content_type or "") or ".png"
    name = f"{hashlib.sha1(data).hexdigest()[:12]}__{safe(Path(filename or 'page').stem)}{ext}"
    path = PAGES / name
    if not path.exists():
        path.write_bytes(data)
    return name


def run_detect(page: str, **kwargs) -> dict:
    path = PAGES / Path(page).name
    if not path.is_file():
        raise HTTPException(404, "unknown page")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    _, result = detect_bytes(path.read_bytes(), mime, **kwargs)
    (RESULTS / f"{path.name}.json").write_text(json.dumps(result, ensure_ascii=False))
    return result


def page_info(name: str) -> dict:
    return {"name": name, "cached": (RESULTS / f"{name}.json").exists()}


def load_volume(name: str) -> dict:
    path = VOLUMES / f"{safe(name)}.json"
    if not path.is_file():
        raise HTTPException(404, "unknown volume")
    vol = json.loads(path.read_text())
    vol["pages"] = [page_info(p) for p in vol["pages"]]
    vol["job"] = JOBS.get(vol["name"])
    return vol


def save_volume(name: str, pages: list[str]) -> None:
    (VOLUMES / f"{safe(name)}.json").write_text(json.dumps({"name": name, "pages": pages}))


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX


@app.get("/models")
def models() -> dict:
    return {"models": list_vision_models(), "default": MODEL, "lang": LANG}


@app.get("/pages")
def pages() -> dict:
    files = sorted(PAGES.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"pages": [page_info(p.name) for p in files]}


@app.post("/pages")
async def upload(image: UploadFile = File(...)) -> dict:
    return {"page": save_page(await image.read(), image.filename, image.content_type)}


@app.get("/results/{page}")
def result(page: str) -> JSONResponse:
    path = RESULTS / f"{Path(page).name}.json"
    if not path.is_file():
        raise HTTPException(404, "no cached result")
    return JSONResponse(json.loads(path.read_text()))


@app.post("/detect")
async def detect(
    page: str = Form(...), model: str = Form(MODEL), thinking: bool = Form(False), lang: str = Form(LANG)
) -> JSONResponse:
    try:
        result = await run_in_threadpool(run_detect, page, model=model, thinking=thinking, lang=lang)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=502)
    return JSONResponse(result)


@app.get("/volumes")
def volumes() -> dict:
    names = sorted(json.loads(p.read_text())["name"] for p in VOLUMES.glob("*.json"))
    return {"volumes": names}


@app.post("/volumes")
def create_volume(name: str = Form(...)) -> dict:
    name = name.strip()
    if not name:
        raise HTTPException(400, "empty name")
    if not (VOLUMES / f"{safe(name)}.json").exists():
        save_volume(name, [])
    return load_volume(name)


@app.get("/volumes/{name}")
def volume(name: str) -> dict:
    return load_volume(name)


@app.get("/samples")
def samples() -> dict:
    return {"samples": list(SAMPLES)}


@app.post("/samples/{book}")
async def import_sample(book: str) -> dict:
    if book not in SAMPLES:
        raise HTTPException(404, "unknown sample")
    name = f"OpenMantra {book}"
    if not (VOLUMES / f"{safe(name)}.json").exists():
        urls = [SAMPLE_URL.format(book=book, page=i) for i in range(SAMPLES[book])]
        downloads = await asyncio.gather(*(run_in_threadpool(read_source, u) for u in urls))
        pages = [save_page(data, f"{book}_{i:03d}.jpg", mime) for i, (data, mime) in enumerate(downloads)]
        save_volume(name, pages)
    return load_volume(name)


@app.post("/volumes/{name}/pages")
async def add_pages(name: str, images: list[UploadFile] = File(...)) -> dict:
    vol = load_volume(name)
    existing = [p["name"] for p in vol["pages"]]
    uploads = sorted(images, key=lambda f: f.filename or "")
    for f in uploads:
        page = save_page(await f.read(), f.filename, f.content_type)
        if page not in existing:
            existing.append(page)
    save_volume(name, existing)
    return load_volume(name)


def translate_volume(name: str, pages: list[str], model: str, thinking: bool, lang: str) -> None:
    job = JOBS[name]
    context = None
    for i, page in enumerate(pages):
        job.update(current=page, done=i)
        try:
            result = run_detect(page, model=model, thinking=thinking, lang=lang, context=context)
            context = [b["text"] for b in result["bubbles"]]
        except Exception as e:
            job["errors"].append(f"{page}: {type(e).__name__}: {e}")
            context = None
    job.update(done=len(pages), current=None, running=False)


@app.post("/volumes/{name}/translate")
def start_translate(
    name: str, model: str = Form(MODEL), thinking: bool = Form(False), lang: str = Form(LANG)
) -> dict:
    vol = load_volume(name)
    if JOBS.get(name, {}).get("running"):
        raise HTTPException(409, "already running")
    pages = [p["name"] for p in vol["pages"]]
    JOBS[name] = {"running": True, "done": 0, "total": len(pages), "current": None, "errors": []}
    threading.Thread(target=translate_volume, args=(name, pages, model, thinking, lang), daemon=True).start()
    return load_volume(name)
