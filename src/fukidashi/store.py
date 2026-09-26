import hashlib
import json
import mimetypes
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from fukidashi.book import BookPage, read_page
from fukidashi.detect import Progress, detect_bytes, no_progress
from fukidashi.memory import Memory, memory_view
from fukidashi.render import render
from fukidashi.settings import settings

PAGES = settings.data_dir / "pages"
RESULTS = settings.data_dir / "results"
VOLUMES = settings.data_dir / "volumes"
RENDERED = settings.data_dir / "rendered"
MEMORY = settings.data_dir / "memory"
MEMORY_BACKOFF = 2


def ensure_dirs() -> None:
    for d in (PAGES, RESULTS, VOLUMES, RENDERED, MEMORY):
        d.mkdir(parents=True, exist_ok=True)


def safe(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name.strip())[:60] or "untitled"


def write_atomic(path: Path, write: Callable[[Path], object]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    write(tmp)
    tmp.replace(path)


def write_json(path: Path, data: Any) -> None:
    write_atomic(
        path, lambda tmp: tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    )


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
    result: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
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
    vol: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    vol["pages"] = [page_info(p) for p in vol["pages"]]
    return vol


def save_volume(name: str, pages: list[str]) -> None:
    write_json(volume_path(name), {"name": name, "pages": pages})


def list_volumes() -> list[str]:
    return sorted(json.loads(p.read_text(encoding="utf-8"))["name"] for p in VOLUMES.glob("*.json"))


def volume_pages(volume: str) -> list[str]:
    vol = load_volume(volume)
    return [p["name"] for p in vol["pages"]] if vol else []


def memory_path(volume: str, model: str, lang: str) -> Path:
    return MEMORY / f"{safe(volume)}__{safe(model)}__{safe(lang)}.json"


def load_snapshots(volume: str, model: str, lang: str) -> dict[str, dict[str, Any]]:
    path = memory_path(volume, model, lang)
    if not path.is_file():
        return {}
    snapshots: dict[str, dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))["snapshots"]
    return snapshots


def save_snapshot(volume: str, page: str, model: str, lang: str, memory: Memory) -> None:
    snapshots = load_snapshots(volume, model, lang)
    snapshots[page] = memory.dump()
    record = {"volume": volume, "model": model, "lang": lang, "snapshots": snapshots}
    write_json(memory_path(volume, model, lang), record)


def latest_snapshot(snapshots: dict[str, dict[str, Any]], pages: list[str]) -> Memory | None:
    for name in reversed(pages):
        if name in snapshots:
            return Memory.model_validate(snapshots[name])
    return None


def memory_before(volume: str, page: str, model: str, lang: str) -> Memory:
    pages = volume_pages(volume)
    earlier = pages[: pages.index(page)] if page in pages else []
    return latest_snapshot(load_snapshots(volume, model, lang), earlier) or Memory()


def volume_memory(volume: str, model: str, lang: str) -> Memory | None:
    return latest_snapshot(load_snapshots(volume, model, lang), volume_pages(volume))


def page_number(volume: str, page: str) -> int:
    pages = volume_pages(volume)
    return pages.index(page) + 1 if page in pages else 1


def has_story(memory: Memory) -> bool:
    return bool(memory.summary or memory.characters or memory.glossary or memory.threads)


def combined_usage(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    counts = {k: v for k, v in second.items() if isinstance(v, int)}
    return {**first, **{k: int(first.get(k) or 0) + v for k, v in counts.items()}}


async def translate_with_memory(
    page: str,
    data: bytes,
    mime: str,
    options: dict[str, Any],
    volume: str,
    on_progress: Progress,
) -> dict[str, Any]:
    model, lang = options["model"], options["lang"]
    memory = memory_before(volume, page, model, lang)
    view = memory_view(memory) if has_story(memory) else None
    _, result = await detect_bytes(data, mime, **options, memory=view, on_progress=on_progress)
    write_json(result_path(page), result)
    boxes = [{"id": f"b{i}", "text": b["text"]} for i, b in enumerate(result["bubbles"], start=1)]
    reading = BookPage(index=page_number(volume, page), image=data, mime=mime, boxes=boxes)
    effort = "low" if options["thinking"] else None
    memory, update = await read_page(reading, memory, model, lang, effort, print, MEMORY_BACKOFF)
    for bubble, box in zip(result["bubbles"], boxes, strict=True):
        bubble["speaker"] = box.get("speaker")
    result["memoryFailed"] = update is None
    if update is not None:
        result["usage"] = combined_usage(result.get("usage") or {}, update.usage)
    save_snapshot(volume, page, model, lang, memory)
    return result


async def translate_page(
    page: str,
    options: dict[str, Any],
    previous_page: str | None = None,
    on_progress: Progress = no_progress,
    volume: str | None = None,
) -> dict[str, Any]:
    path = PAGES / page
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    data = path.read_bytes()
    if volume and settings.volume_memory:
        result = await translate_with_memory(page, data, mime, options, volume, on_progress)
    else:
        previous = load_result(previous_page) if previous_page else None
        context = [b["text"] for b in previous["bubbles"]] if previous else None
        _, result = await detect_bytes(
            data, mime, **options, context=context, on_progress=on_progress
        )
    write_json(result_path(page), result)
    return result
