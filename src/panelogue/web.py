from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.concurrency import run_in_threadpool

from panelogue.detect import MODEL, detect_bytes, list_vision_models

load_dotenv()
app = FastAPI()
INDEX = (Path(__file__).parent / "static" / "index.html").read_text()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return INDEX


@app.get("/models")
def models() -> dict:
    return {"models": list_vision_models(), "default": MODEL}


@app.post("/detect")
async def detect(image: UploadFile = File(...), model: str = Form(MODEL), thinking: bool = Form(False)) -> JSONResponse:
    data = await image.read()
    try:
        _, result = await run_in_threadpool(detect_bytes, data, image.content_type or "image/png", model, thinking)
    except Exception as e:
        return JSONResponse({"error": f"{type(e).__name__}: {e}"}, status_code=502)
    return JSONResponse(result)
