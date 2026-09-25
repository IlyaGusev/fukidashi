import asyncio
import json
import re
from io import BytesIO
from pathlib import Path
from statistics import median
from typing import Any

import fire
from PIL import Image

from fukidashi.book import BookOptions, BookPage, translate_book
from fukidashi.detect import read_source
from fukidashi.memory import Memory
from fukidashi.settings import settings

REPO = "https://raw.githubusercontent.com/mantra-inc/open-mantra-dataset/main/"
OUT = Path("out/books")
CREDIT = (
    "OpenMantra dataset (Mantra Inc.), CC BY-NC 4.0. Reference English by professional translators."
)


def fetch_cached(path: str) -> bytes:
    local = OUT / "cache" / path
    if not local.exists():
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(read_source(REPO + path)[0])
    return local.read_bytes()


def bubble_background(img: Image.Image, bbox: list[int]) -> str:
    x1, y1, x2, y2 = bbox
    rgb = img.convert("RGB")
    samples = [
        rgb.getpixel((x, y))
        for x in range(x1, x2, max(1, (x2 - x1) // 12))
        for y in (y1 + 1, y2 - 2)
        if 0 <= x < img.width and 0 <= y < img.height
    ]
    if not samples:
        return "#FFFFFF"
    r, g, b = (int(median(channel)) for channel in zip(*samples, strict=False))
    return f"#{r:02X}{g:02X}{b:02X}"


def load_book(
    book: str, first: int, count: int | None
) -> tuple[list[BookPage], list[dict[str, Any]]]:
    annotation = json.loads(fetch_cached("annotation.json"))
    raw_pages = next(b for b in annotation if b["book_title"] == book)["pages"]
    raw_pages = raw_pages[first : first + count] if count else raw_pages[first:]
    pages: list[BookPage] = []
    meta: list[dict[str, Any]] = []
    for number, raw in enumerate(raw_pages, start=1):
        rel = raw["image_paths"]["ja"]
        data = fetch_cached(rel)
        img = Image.open(BytesIO(data))
        boxes = []
        for i, t in enumerate(raw["text"], start=1):
            bbox = [t["x"], t["y"], t["x"] + t["w"], t["y"] + t["h"]]
            boxes.append(
                {
                    "id": f"p{number}b{i}",
                    "bbox": bbox,
                    "kind": "speech",
                    "text": t["text_ja"],
                    "reference": t["text_en"],
                    "bg": bubble_background(img, bbox),
                }
            )
        pages.append(BookPage(index=number, image=data, mime="image/jpeg", boxes=boxes))
        meta.append(
            {"index": number, "imageUrl": REPO + rel, "width": img.width, "height": img.height}
        )
    return pages, meta


def load_seed(path: str, after: int | None) -> Memory:
    snapshots = json.loads(Path(path).read_text(encoding="utf-8"))["snapshots"]
    by_page = {s["afterPage"]: s for s in snapshots}
    if after is not None and after not in by_page:
        raise SystemExit(f"{path} has no memory snapshot after page {after}")
    return Memory.model_validate(snapshots[-1] if after is None else by_page[after])


def run_suffix(seed: str | None, options: BookOptions) -> str:
    return (
        ("_seeded" if seed else "")
        + ("" if options.memory else "_nomemory")
        + (f"_recent{options.recent_pages}" if options.recent_pages else "")
        + ("" if options.second_pass else "_nopass2")
    )


def summary(result: dict[str, Any]) -> dict[str, Any]:
    stats = result["stats"]
    return {
        "pages": len(stats),
        "memoryFailed": sum(s["memoryFailed"] for s in stats),
        "translateFailed": sum(s["translateFailed"] for s in stats),
        "maxViewChars": max(s["viewChars"] for s in stats),
        "maxStoredChars": max(s["storedChars"] for s in stats),
        "maxPatchChars": max(s["patchChars"] for s in stats),
        "finalGlossary": stats[-1]["glossary"],
        "glossaryNeverShrank": all(
            b["glossary"] >= a["glossary"] for a, b in zip(stats, stats[1:], strict=False)
        ),
        "firstConfidence": stats[0]["confidence"],
        "finalConfidence": stats[-1]["confidence"],
        "revisedInPass2": result["revised"],
        "usage": result["usage"],
    }


def main(
    book: str = "tencho_isoro",
    first: int = 0,
    count: int | None = None,
    model: str = settings.model,
    lang: str = settings.lang,
    seed: str | None = None,
    seed_after: int | None = None,
    name: str | None = None,
    memory: bool = True,
    recent_pages: int = 0,
    second_pass: bool = True,
) -> None:
    options = BookOptions(memory, recent_pages, second_pass)
    model_slug = re.sub(r"[^\w.-]", "_", model.split("/")[-1])
    name = name or f"{book}_{first}-{count or 'end'}_{model_slug}" + run_suffix(seed, options)
    pages, meta = load_book(book, first, count)
    print(f"{book}: {len(pages)} pages from page {first + 1}, model {model}", flush=True)
    result = asyncio.run(
        translate_book(
            pages,
            OUT / f"{name}.checkpoint.json",
            model,
            lang,
            load_seed(seed, seed_after) if seed else None,
            log=lambda line: print(line, flush=True),
            options=options,
        )
    )
    volume = {
        "id": f"openmantra-{name}",
        "title": book.replace("_", " ").title(),
        "credit": CREDIT,
        "sourceLang": "Japanese",
        "targetLang": lang,
        "pages": [{**m, "bubbles": p["boxes"]} for m, p in zip(meta, pages, strict=True)],
        "snapshots": result["snapshots"],
        "memoryStats": result["stats"],
        "summary": summary(result),
        "models": {"detect": "OpenMantra boxes", "memory": model, "translate": model},
        "seededFrom": seed,
        "seededAfterPage": seed_after,
        "options": options._asdict(),
    }
    out = OUT / f"{name}.json"
    out.write_text(json.dumps(volume, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(volume["summary"], indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    fire.Fire(main)
