import hashlib
import json
import mimetypes
import re
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from panelogue.detect import MODEL, detect_bytes, list_vision_models

load_dotenv()
app = FastAPI()
INDEX = (Path(__file__).parent / "static" / "index.html").read_text()
PAGES = Path("data/pages")
RESULTS = Path("data/results")
PAGES.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)
app.mount("/pages/files", StaticFiles(directory=PAGES), name="pages")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX


@app.get("/models")
def models() -> dict:
    return {"models": list_vision_models(), "default": MODEL}


@app.get("/pages")
def pages() -> dict:
    files = sorted(PAGES.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return {"pages": [{"name": p.name, "cached": (RESULTS / f"{p.name}.json").exists()} for p in files]}


@app.get("/results/{page}")
def result(page: str) -> JSONResponse:
    path = RESULTS / f"{Path(page).name}.json"
    if not path.is_file():
        raise HTTPException(404, "no cached result")
    return JSONResponse(json.loads(path.read_text()))


@app.post("/pages")
async def upload(image: UploadFile = File(...)) -> dict:
    data = await image.read()
    ext = Path(image.filename or "").suffix or mimetypes.guess_extension(image.content_type or "") or ".png"
    stem = re.sub(r"[^\w.-]+", "_", Path(image.filename or "page").stem)[:60]
    name = f"{hashlib.sha1(data).hexdigest()[:12]}__{stem}{ext}"
    path = PAGES / name
    if not path.exists():
        path.write_bytes(data)
    return {"page": name}


@app.post("/detect")
async def detect(page: str = Form(...), model: str = Form(MODEL), thinking: bool = Form(False)) -> JSONResponse:
    path = PAGES / Path(page).name
    if not path.is_file():
        raise HTTPException(404, "unknown page")
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    try:
        _, result = await run_in_threadpool(detect_bytes, path.read_bytes(), mime, model, thinking)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=502)
    (RESULTS / f"{path.name}.json").write_text(json.dumps(result, ensure_ascii=False))
    return JSONResponse(result)
