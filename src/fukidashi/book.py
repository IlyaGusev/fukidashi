import asyncio
import json
from collections.abc import Awaitable, Callable
from functools import partial
from pathlib import Path
from typing import Any, TypedDict

from fukidashi.jobs import RETRYABLE
from fukidashi.memory import (
    Memory,
    MemoryUpdate,
    carry_over,
    complete_json,
    image_part,
    memory_view,
    update_memory,
)
from fukidashi.settings import settings

TRANSLATE_PROMPT = """\
Translate the text boxes of this manga page into {lang} for a published edition.
{pass_note}

Story memory:
{memory}

Text boxes (id | speaker | source text | max_chars{first_pass_column}):
{boxes}

Keep each character's voice from the memory, use the glossary renderings exactly, keep jokes
working in {lang} and stay within max_chars so the text fits the bubble. Sound effects become
natural {lang} sound effects. memory_refs are the ids of the memory entries you relied on.
{reason_rule}
Answer JSON only:
{{"translations": [{{"id": "", "translation": "", "reason": null, "memory_refs": []}}]}}
"""

FIRST_PASS_NOTE = "FIRST PASS. Only the pages read so far are known."
FIRST_PASS_RULE = "reason is null."
SECOND_PASS_NOTE = (
    "SECOND PASS. You now know the WHOLE volume. Each box shows the first-pass translation made "
    "when only earlier pages were known. Keep it unless the full story shows it should change."
)
SECOND_PASS_RULE = (
    "If you change a translation, reason is one short sentence naming what a later page taught "
    "you, e.g. 'Learned on p.4 that ...'. If unchanged, reason is null and translation is the "
    "first-pass text exactly."
)
SECOND_PASS_BATCH = 3

Log = Callable[[str], None]


class BookPage(TypedDict):
    index: int
    image: bytes
    mime: str
    boxes: list[dict[str, Any]]


def max_chars(text: str) -> int:
    return int(len(text) * 1.25) + 6


def box_lines(boxes: list[dict[str, Any]], second_pass: bool) -> str:
    rows = []
    for b in boxes:
        row = f"- {b['id']} | {b.get('speaker')} | {b['text']!r} | {max_chars(b['text'])}"
        if second_pass:
            row += f" | {b.get('firstPassTranslation')!r}"
        rows.append(row)
    return "\n".join(rows)


def translation_items(result: Any) -> list[dict[str, Any]]:
    items: Any = result.get("translations") if isinstance(result, dict) else result
    if isinstance(items, list):
        return [t for t in items if isinstance(t, dict) and "id" in t]
    if isinstance(result, dict):
        return [{"id": k, "translation": v} for k, v in result.items() if isinstance(v, str)]
    return []


def add_usage(total: dict[str, int], usage: dict[str, Any]) -> None:
    total["calls"] = total.get("calls", 0) + 1
    for field in ("prompt_tokens", "completion_tokens"):
        total[field] = total.get(field, 0) + int(usage.get(field) or 0)


async def translate_boxes(
    page: BookPage, memory: Memory, model: str, lang: str, second_pass: bool
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not page["boxes"]:
        return {}, {}
    prompt = TRANSLATE_PROMPT.format(
        lang=lang,
        pass_note=SECOND_PASS_NOTE if second_pass else FIRST_PASS_NOTE,
        memory=memory_view(memory),
        first_pass_column=" | first pass" if second_pass else "",
        boxes=box_lines(page["boxes"], second_pass),
        reason_rule=SECOND_PASS_RULE if second_pass else FIRST_PASS_RULE,
    )
    content = [image_part(page["image"], page["mime"]), {"type": "text", "text": prompt}]
    data, _, usage = await complete_json(content, model)
    return {str(t["id"]): t for t in translation_items(data)}, usage


async def with_retries[T](
    call: Callable[[], Awaitable[T]], what: str, log: Log, backoff: float
) -> T:
    for attempt in range(1, settings.attempts + 1):
        try:
            async with asyncio.timeout(settings.step_timeout):
                return await call()
        except RETRYABLE as e:
            if attempt == settings.attempts:
                raise
            log(f"  retry {attempt} {what}: {type(e).__name__}: {e}")
            await asyncio.sleep(backoff * 2 ** (attempt - 1))
    raise ValueError("settings.attempts must be at least 1")


def page_stats(memory: Memory, update: MemoryUpdate | None) -> dict[str, Any]:
    return {
        "page": memory.after_page,
        "confidence": memory.confidence,
        "storedChars": len(json.dumps(memory.dump(), ensure_ascii=False)),
        "viewChars": len(memory_view(memory)),
        "patchChars": update.patch_chars if update else 0,
        "characters": len(memory.characters),
        "glossary": len(memory.glossary),
        "openQuestions": sum(1 for q in memory.questions if q.is_open),
        "memoryFailed": update is None,
        "translateFailed": False,
    }


def load_checkpoint(path: Path) -> dict[str, Any]:
    if path.exists():
        state: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return state
    return {"snapshots": [], "stats": [], "boxes": {}, "usage": {}}


def save_checkpoint(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")


def starting_memory(state: dict[str, Any], seed: Memory | None) -> Memory:
    if state["snapshots"]:
        return Memory.model_validate(state["snapshots"][-1])
    return carry_over(seed) if seed else Memory()


async def read_page(
    page: BookPage, memory: Memory, model: str, lang: str, log: Log, backoff: float
) -> tuple[Memory, MemoryUpdate | None]:
    call = partial(
        update_memory,
        memory,
        page["index"],
        page["image"],
        page["mime"],
        page["boxes"],
        model,
        lang,
    )
    try:
        update = await with_retries(call, f"memory p{page['index']}", log, backoff)
    except RETRYABLE as e:
        log(f"memory p{page['index']} FAILED: {type(e).__name__}: {e}")
        failed = f"Memory update failed on this page: {type(e).__name__}"
        return memory.model_copy(update={"after_page": page["index"], "changes": [failed]}), None
    for b in page["boxes"]:
        b["speaker"] = update.speakers.get(b["id"])
    return update.memory, update


async def first_pass(
    page: BookPage, memory: Memory, model: str, lang: str, log: Log, backoff: float
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]] | None:
    call = partial(translate_boxes, page, memory, model, lang, False)
    try:
        return await with_retries(call, f"translate p{page['index']}", log, backoff)
    except RETRYABLE as e:
        log(f"translate p{page['index']} FAILED: {type(e).__name__}: {e}")
        return None


def apply_first_pass(page: BookPage, translations: dict[str, dict[str, Any]]) -> None:
    for b in page["boxes"]:
        t = translations.get(b["id"], {})
        b["firstPassTranslation"] = str(t.get("translation") or "")
        b["translation"] = b["firstPassTranslation"]
        b["reason"] = None
        b["memoryRefs"] = t.get("memory_refs") or []


def apply_second_pass(page: BookPage, translations: dict[str, dict[str, Any]]) -> int:
    revised = 0
    for b in page["boxes"]:
        t = translations.get(b["id"])
        if not t or not t.get("translation"):
            continue
        b["translation"] = str(t["translation"])
        changed = b["translation"].strip() != b["firstPassTranslation"].strip()
        b["reason"] = t.get("reason") if changed else None
        b["memoryRefs"] = t.get("memory_refs") or b["memoryRefs"]
        revised += changed
    return revised


async def second_pass(
    pages: list[BookPage], memory: Memory, model: str, lang: str, log: Log, backoff: float
) -> tuple[int, dict[str, int]]:
    usage: dict[str, int] = {}

    async def revise(page: BookPage) -> int:
        call = partial(translate_boxes, page, memory, model, lang, True)
        try:
            translations, page_usage = await with_retries(
                call, f"pass 2 p{page['index']}", log, backoff
            )
        except RETRYABLE as e:
            log(f"pass 2 p{page['index']} skipped: {type(e).__name__}: {e}")
            return 0
        add_usage(usage, page_usage)
        return apply_second_pass(page, translations)

    revised = 0
    for start in range(0, len(pages), SECOND_PASS_BATCH):
        batch = pages[start : start + SECOND_PASS_BATCH]
        revised += sum(await asyncio.gather(*(revise(p) for p in batch)))
        log(f"pass 2 done through p{batch[-1]['index']}")
    return revised, usage


async def translate_book(
    pages: list[BookPage],
    checkpoint: Path,
    model: str = settings.model,
    lang: str = settings.lang,
    seed: Memory | None = None,
    log: Log = print,
    backoff: float = 2,
) -> dict[str, Any]:
    state = load_checkpoint(checkpoint)
    memory = starting_memory(state, seed)
    for page in pages:
        saved = state["boxes"].get(str(page["index"]))
        if saved is not None:
            page["boxes"] = saved
            continue
        memory, update = await read_page(page, memory, model, lang, log, backoff)
        stats = page_stats(memory, update)
        if update is not None:
            add_usage(state["usage"], update.usage)
        translated = await first_pass(page, memory, model, lang, log, backoff)
        stats["translateFailed"] = translated is None
        translations, usage = translated or ({}, {})
        if translated is not None:
            add_usage(state["usage"], usage)
        apply_first_pass(page, translations)
        state["snapshots"].append(memory.dump())
        state["stats"].append(stats)
        state["boxes"][str(page["index"])] = page["boxes"]
        save_checkpoint(checkpoint, state)
        log(
            f"p{page['index']:>3} conf {memory.confidence:>3} view {stats['viewChars']:>6} "
            f"stored {stats['storedChars']:>6} patch {stats['patchChars']:>5} "
            f"glossary {stats['glossary']:>3}"
            + (" MEMORY FAILED" if update is None else "")
            + (" TRANSLATE FAILED" if translated is None else "")
        )
    revised, pass2_usage = await second_pass(pages, memory, model, lang, log, backoff)
    usage = dict(state["usage"])
    for field, value in pass2_usage.items():
        usage[field] = usage.get(field, 0) + value
    return {
        "snapshots": state["snapshots"],
        "stats": state["stats"],
        "usage": usage,
        "revised": revised,
    }
