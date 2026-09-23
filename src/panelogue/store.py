import hashlib
import json
import mimetypes
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from panelogue.detect import Progress, detect_bytes, no_progress
from panelogue.render import render
from panelogue.settings import settings

PAGES = settings.data_dir / "pages"
RESULTS = settings.data_dir / "results"
VOLUMES = settings.data_dir / "volumes"
RENDERED = settings.data_dir / "rendered"


def ensure_dirs() -> None:
    for d in (PAGES, RESULTS, VOLUMES, RENDERED):
        d.mkdir(parents=True, exist_ok=True)


def safe(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name.strip())[:60] or "untitled"


def write_atomic(path: Path, write: Callable[[Path], object]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    write(tmp)
    tmp.replace(path)


def write_json(path: Path, data: Any) -> None:
    write_atomic(path, lambda tmp: tmp.write_text(json.dumps(data, ensure_ascii=False)))


def save_page(data: bytes, filename: str | None, content_type: str | None) -> str:
    ext = Path(filename or "").suffix or mimetypes.guess_extension(content_type or "") or ".png"
    name = f"{hashlib.sha1(data).hexdigest()[:12]}__{safe(Path(filename or 'page').stem)}{ext}"
    path = PAGES / name
    if not path.exists():
        path.write_bytes(data)
    return name


def page_exists(name: str) -> bool:
    return (PAGES / name).is_file()


def result_path(page: str) -> Path:
    return RESULTS / f"{page}.json"


def load_result(page: str) -> dict[str, Any] | None:
    path = result_path(page)
    if not path.is_file():
        return None
    result: dict[str, Any] = json.loads(path.read_text())
    return result


def rendered_path(page: str) -> Path:
    return RENDERED / f"{page}.png"


def render_page(page: str) -> Path | None:
    result = load_result(page)
    if result is None:
        return None
    target = rendered_path(page)
    if not target.is_file() or target.stat().st_mtime < result_path(page).stat().st_mtime:
        image = render(Image.open(PAGES / page), result["bubbles"])
        write_atomic(target, lambda tmp: image.save(tmp, "PNG"))
    return target


def page_info(name: str) -> dict[str, Any]:
    return {"name": name, "cached": result_path(name).exists()}


def list_pages() -> list[dict[str, Any]]:
    files = sorted(PAGES.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    return [page_info(p.name) for p in files]


def volume_path(name: str) -> Path:
    return VOLUMES / f"{safe(name)}.json"


def load_volume(name: str) -> dict[str, Any] | None:
    path = volume_path(name)
    if not path.is_file():
        return None
    vol: dict[str, Any] = json.loads(path.read_text())
    vol["pages"] = [page_info(p) for p in vol["pages"]]
    return vol


def save_volume(name: str, pages: list[str]) -> None:
    write_json(volume_path(name), {"name": name, "pages": pages})


def list_volumes() -> list[str]:
    return sorted(json.loads(p.read_text())["name"] for p in VOLUMES.glob("*.json"))


async def translate_page(
    page: str,
    options: dict[str, Any],
    previous_page: str | None = None,
    on_progress: Progress = no_progress,
) -> dict[str, Any]:
    path = PAGES / page
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    previous = load_result(previous_page) if previous_page else None
    context = [b["text"] for b in previous["bubbles"]] if previous else None
    _, result = await detect_bytes(
        path.read_bytes(), mime, **options, context=context, on_progress=on_progress
    )
    write_json(result_path(page), result)
    return result
