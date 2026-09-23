import asyncio
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

import fire
from sacrebleu.metrics.chrf import CHRF

from panelogue.detect import detect_bytes, list_vision_models, read_source
from panelogue.settings import settings

REPO = "https://raw.githubusercontent.com/mantra-inc/open-mantra-dataset/main/"
OUT = Path("out/bench")
COLUMNS = [
    "model",
    "pages",
    "errors",
    "precision",
    "recall",
    "f1",
    "cer",
    "chrf_matched",
    "chrf_page",
    "sec_per_page",
    "tokens_per_page",
]

Box = list[int]
Page = dict[str, Any]


def fetch_cached(path: str) -> bytes:
    local = OUT / "cache" / path
    if not local.exists():
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_bytes(read_source(REPO + path)[0])
    return local.read_bytes()


def load_pages(books: list[str] | None, pages_per_book: int) -> list[Page]:
    annotation = json.loads(fetch_cached("annotation.json"))
    pages = []
    for book in annotation:
        if books and book["book_title"] not in books:
            continue
        candidates = [p for p in book["pages"] if p["text"]]
        step = max(1, len(candidates) // pages_per_book)
        for p in candidates[::step][:pages_per_book]:
            gold = [
                {
                    "bbox": [t["x"], t["y"], t["x"] + t["w"], t["y"] + t["h"]],
                    "ja": t["text_ja"],
                    "en": t["text_en"],
                }
                for t in p["text"]
            ]
            pages.append(
                {"book": book["book_title"], "image": p["image_paths"]["ja"], "gold": gold}
            )
    return pages


def run_path(model: str, page: Page) -> Path:
    model_dir = re.sub(r"[^\w.-]", "_", model)
    return OUT / "runs" / model_dir / f"{page['book']}_{Path(page['image']).stem}.json"


async def run_one(
    model: str, page: Page, thinking: bool, lang: str, sem: asyncio.Semaphore
) -> None:
    path = run_path(model, page)
    if path.exists():
        return
    data = fetch_cached(page["image"])
    async with sem:
        start = time.monotonic()
        try:
            _, result = await detect_bytes(data, "image/jpeg", model, thinking, lang)
            record: dict[str, Any] = {"result": result}
        except Exception as e:  # noqa: BLE001
            record = {"error": f"{type(e).__name__}: {e}"}
        record["seconds"] = time.monotonic() - start
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1))
    status = record.get("error") or f"{len(record['result']['bubbles'])} boxes"
    print(f"{model:32} {page['image']:40} {record['seconds']:6.1f}s  {status}", flush=True)


def iou(a: Box, b: Box) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


def text_similarity(a: str, b: str) -> float:
    longest = max(len(a), len(b))
    return 1 - edit_distance(a, b) / longest if longest else 0.0


def match(
    gold: list[dict[str, Any]], pred: list[dict[str, Any]], by: str, threshold: float
) -> list[tuple[int, int]]:
    if by == "box":
        scores = [
            (iou(g["bbox"], p["bbox"]), gi, pi)
            for gi, g in enumerate(gold)
            for pi, p in enumerate(pred)
        ]
    else:
        scores = [
            (text_similarity(norm_ja(g["ja"]), norm_ja(str(p.get("text", "")))), gi, pi)
            for gi, g in enumerate(gold)
            for pi, p in enumerate(pred)
        ]
    pairs = sorted(scores, reverse=True)
    used_gold: set[int] = set()
    used_pred: set[int] = set()
    matched = []
    for score, gi, pi in pairs:
        if score < threshold:
            break
        if gi not in used_gold and pi not in used_pred:
            matched.append((gi, pi))
            used_gold.add(gi)
            used_pred.add(pi)
    return matched


def norm_ja(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def score_model(model: str, pages: list[Page], by: str, threshold: float) -> dict[str, Any]:
    n_gold = n_pred = n_match = errors = edits = gold_chars = 0
    seconds: list[float] = []
    tokens: list[int] = []
    hyp_boxes: list[str] = []
    ref_boxes: list[str] = []
    hyp_pages: list[str] = []
    ref_pages: list[str] = []
    for page in pages:
        record = json.loads(run_path(model, page).read_text())
        seconds.append(record["seconds"])
        gold = page["gold"]
        n_gold += len(gold)
        ref_pages.append(" ".join(g["en"].lower() for g in gold))
        if "error" in record:
            errors += 1
            hyp_pages.append("")
            continue
        bubbles = record["result"]["bubbles"]
        tokens.append(record["result"].get("usage", {}).get("completion_tokens", 0))
        n_pred += len(bubbles)
        hyp_pages.append(" ".join(str(b.get("translation", "")).lower() for b in bubbles))
        for gi, pi in match(gold, bubbles, by, threshold):
            n_match += 1
            ref_ja = norm_ja(gold[gi]["ja"])
            edits += edit_distance(ref_ja, norm_ja(str(bubbles[pi].get("text", ""))))
            gold_chars += len(ref_ja)
            ref_boxes.append(gold[gi]["en"].lower())
            hyp_boxes.append(str(bubbles[pi].get("translation", "")).lower())
    precision = n_match / n_pred if n_pred else 0.0
    recall = n_match / n_gold if n_gold else 0.0
    chrf = CHRF()
    return {
        "model": model,
        "pages": len(pages),
        "errors": errors,
        "precision": precision,
        "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if n_match else 0.0,
        "cer": edits / gold_chars if gold_chars else 1.0,
        "chrf_matched": chrf.corpus_score(hyp_boxes, [ref_boxes]).score if hyp_boxes else 0.0,
        "chrf_page": chrf.corpus_score(hyp_pages, [ref_pages]).score,
        "sec_per_page": sum(seconds) / len(seconds),
        "tokens_per_page": sum(tokens) / len(tokens) if tokens else 0.0,
    }


def print_table(rows: list[dict[str, Any]]) -> None:
    print("| " + " | ".join(COLUMNS) + " |")
    print("|" + "---|" * len(COLUMNS))
    for r in sorted(rows, key=lambda r: -r["chrf_page"]):
        cells = [f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c]) for c in COLUMNS]
        print("| " + " | ".join(cells) + " |")


async def run_all(
    models: list[str], pages: list[Page], thinking: bool, lang: str, concurrency: int
) -> None:
    sem = asyncio.Semaphore(concurrency)
    await asyncio.gather(*(run_one(m, p, thinking, lang, sem) for m in models for p in pages))


def main(
    models: str | list[str] | None = None,
    books: str | list[str] | None = None,
    pages_per_book: int = 4,
    match_by: str = "box",
    threshold: float = 0.5,
    thinking: bool = False,
    lang: str = settings.lang,
    concurrency: int = 4,
) -> None:
    model_list = (
        [models] if isinstance(models, str) else models or asyncio.run(list_vision_models())
    )
    book_list = [books] if isinstance(books, str) else books
    pages = load_pages(book_list, pages_per_book)
    print(f"{len(pages)} pages x {len(model_list)} models", flush=True)
    asyncio.run(run_all(model_list, pages, thinking, lang, concurrency))
    rows = [score_model(m, pages, match_by, threshold) for m in model_list]
    (OUT / "summary.json").write_text(json.dumps(rows, indent=1))
    print_table(rows)


if __name__ == "__main__":
    fire.Fire(main)
