import asyncio
import json
import re
import time
import unicodedata
from pathlib import Path
from typing import Any

import fire
from sacrebleu.metrics.chrf import CHRF

from fukidashi.detect import client, detect_bytes, list_vision_models, read_source
from fukidashi.settings import settings

REPO = "https://raw.githubusercontent.com/mantra-inc/open-mantra-dataset/main/"
OUT = Path("out/bench")
EXTRA_MODELS = ["google/gemma-3-27b-it"]
EXTRA_REASONING_MODELS = {"deepseek-ai/DeepSeek-V4.1-Flash"}
OFF = "off"
PROMPT_ROOM = 4096
COLUMNS = [
    "model",
    "effort",
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
Run = tuple[str, str]
RunConfig = tuple[str, str, int]


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


async def catalog() -> dict[str, dict[str, Any]]:
    models = (await client().models.list(extra_query={"verbose": "true"})).data
    return {m.id: m.model_extra or {} for m in models}


def reasoning_models(models: dict[str, dict[str, Any]]) -> set[str]:
    thinkers = {
        m for m, info in models.items() if "reasoning" in (info.get("supported_features") or [])
    }
    return thinkers | EXTRA_REASONING_MODELS


def fit_max_tokens(max_tokens: int, info: dict[str, Any]) -> int:
    return min(max_tokens, int(info["context_length"]) - PROMPT_ROOM)


def run_path(model: str, effort: str, page: Page) -> Path:
    model_dir = re.sub(r"[^\w.-]", "_", model)
    return OUT / "runs" / model_dir / effort / f"{page['book']}_{Path(page['image']).stem}.json"


async def run_one(run: RunConfig, page: Page, lang: str, sem: asyncio.Semaphore) -> None:
    model, effort, max_tokens = run
    path = run_path(model, effort, page)
    if path.exists():
        return
    data = fetch_cached(page["image"])
    async with sem:
        start = time.monotonic()
        try:
            async with asyncio.timeout(settings.step_timeout):
                _, result = await detect_bytes(
                    data,
                    "image/jpeg",
                    model,
                    thinking=effort != OFF,
                    lang=lang,
                    effort=None if effort == OFF else effort,
                    max_tokens=max_tokens,
                )
            record: dict[str, Any] = {"result": result}
        except Exception as e:  # noqa: BLE001
            record = {"error": f"{type(e).__name__}: {e}"}
        record["seconds"] = time.monotonic() - start
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    status = record.get("error") or f"{len(record['result']['bubbles'])} boxes"
    print(
        f"{model:32} {effort:7} {page['image']:36} {record['seconds']:6.1f}s  {status}", flush=True
    )


def iou(a: Box, b: Box) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


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
    used_gold: set[int] = set()
    used_pred: set[int] = set()
    matched = []
    for score, gi, pi in sorted(scores, reverse=True):
        if score < threshold:
            break
        if gi not in used_gold and pi not in used_pred:
            matched.append((gi, pi))
            used_gold.add(gi)
            used_pred.add(pi)
    return matched


def score_run(run: Run, pages: list[Page], by: str, threshold: float) -> dict[str, Any]:
    model, effort = run
    n_gold = n_pred = n_match = errors = edits = gold_chars = 0
    seconds: list[float] = []
    tokens: list[int] = []
    hyp_boxes: list[str] = []
    ref_boxes: list[str] = []
    hyp_pages: list[str] = []
    ref_pages: list[str] = []
    for page in pages:
        record = json.loads(run_path(model, effort, page).read_text(encoding="utf-8"))
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
        "effort": effort,
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


async def plan_runs(
    models: list[str] | None, efforts: list[str], max_tokens: int
) -> list[RunConfig]:
    model_list = models or sorted(set(await list_vision_models()) | set(EXTRA_MODELS))
    info = await catalog()
    thinkers = reasoning_models(info)
    return [
        (m, e, fit_max_tokens(max_tokens, info[m]))
        for m in model_list
        for e in efforts
        if e == OFF or m in thinkers
    ]


async def run_all(
    models: list[str] | None,
    efforts: list[str],
    max_tokens: int,
    pages: list[Page],
    lang: str,
    concurrency: int,
) -> list[Run]:
    runs = await plan_runs(models, efforts, max_tokens)
    print(f"{len(pages)} pages x {len(runs)} runs", flush=True)
    sem = asyncio.Semaphore(concurrency)
    await asyncio.gather(*(run_one(r, p, lang, sem) for p in pages for r in runs))
    return [(model, effort) for model, effort, _ in runs]


def as_list(value: str | list[str] | None) -> list[str] | None:
    return value.split(",") if isinstance(value, str) else value


def main(
    models: str | list[str] | None = None,
    books: str | list[str] | None = None,
    efforts: str | list[str] = "off,low,medium",
    pages_per_book: int = 10,
    max_tokens: int = 65536,
    threshold: float = 0.5,
    lang: str = settings.lang,
    concurrency: int = 6,
) -> None:
    pages = load_pages(as_list(books), pages_per_book)
    runs = asyncio.run(
        run_all(as_list(models), as_list(efforts) or [OFF], max_tokens, pages, lang, concurrency)
    )
    summary = {}
    for by in ("box", "text"):
        rows = [score_run(r, pages, by, threshold) for r in runs]
        summary[by] = rows
        print(f"\nmatched by {by} (threshold {threshold}):")
        print_table(rows)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    fire.Fire(main)
