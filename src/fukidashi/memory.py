import base64
import json
import re
from collections.abc import Callable
from typing import Any, NamedTuple

from pydantic import BaseModel, ConfigDict, ValidationError, model_validator
from pydantic.alias_generators import to_camel

from fukidashi.detect import BadOutput, Progress, no_progress, stream_with_optional, strip_fence
from fukidashi.settings import settings

DESCRIPTION_CHARS = 300
VOICE_CHARS = 200
NOTE_CHARS = 200
SUMMARY_CHARS = 600
MAX_CHANGES = 4
PATCH_MAX_TOKENS = 16000
PAID_OFF_WORDS = ("paid", "resolv", "clos", "done")

MEMORY_PROMPT = """\
You are the story editor of a manga localization studio. You read a volume page by page and
keep a STORY MEMORY that a translator into {lang} relies on.

{memory_title}:
{memory}

Page {page} is attached. Its text boxes (id | source text):
{boxes}

Reply with a PATCH, not the whole memory. Include only entries that are new on this page or
that this page changes. Every entry you leave out is kept exactly as it is.
- characters: {{"id": "c_short", "name": "", "description": "", "voice": "", "firstSeenPage": {page}}}.
  description is who they are now (look, role, relationships) in at most 300 characters, not a
  log of pages. voice is how they talk, with one example phrase. Reuse existing ids.
- glossary: {{"source": "", "target": "", "note": ""}} only for words that must read the same
  every time: names of people, places, groups, techniques and items, invented terms, titles used
  as names, and a character's recurring catchphrase. Never everyday words, pronouns, greetings,
  interjections, laughs, sound effects, verb endings or one-off phrases: the translator renders
  those fresh in context. Keep existing targets unless this page proves them wrong.
- threads: {{"id": "t_short", "note": "", "status": "open|paid_off", "pages": [{page}]}}.
- questions: a new ambiguity is {{"id": "q_short", "question": ""}}. To resolve an open question,
  send its id with "answer" and "resolvedOnPage": {page}.
- speakers: for EVERY text box id on this page, who says it: a character name, "narrator", or
  null for a sound effect.
- changes: 1-4 short lines on what changed in your understanding on this page.
- confidence: 0-100, how well you understand the story so far.
- summary: the story so far in at most 3 sentences.

Answer JSON only:
{{"confidence": 0, "summary": "", "characters": [], "glossary": [], "threads": [],
"questions": [], "changes": [], "speakers": {{}}}}
"""  # noqa: E501

FIRST_PAGE_TITLE = "Story memory before page {page}"
SEEDED_TITLE = "Story memory carried over from the previous chapters, before page {page}"


def clip(text: str, limit: int) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    if limit <= 1:
        return ""
    head = text[: limit - 1]
    return (head.rsplit(" ", 1)[0] if " " in head else head) + "…"


def slug(text: str) -> str:
    return re.sub(r"\W+", "_", text.strip().lower()).strip("_") or "unnamed"


class Entry(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


class Character(Entry):
    id: str
    name: str = ""
    description: str = ""
    voice: str = ""
    first_seen_page: int | None = None

    @model_validator(mode="before")
    @classmethod
    def id_from_name(cls, data: Any) -> Any:
        if isinstance(data, dict) and not data.get("id") and data.get("name"):
            return {**data, "id": "c_" + slug(str(data["name"]))}
        return data


class Term(Entry):
    source: str
    target: str = ""
    note: str = ""


class Thread(Entry):
    id: str
    note: str = ""
    status: str = "open"
    pages: list[int] = []

    @model_validator(mode="before")
    @classmethod
    def normalize_status(cls, data: Any) -> Any:
        if isinstance(data, dict) and data.get("status"):
            closed = any(word in str(data["status"]).lower() for word in PAID_OFF_WORDS)
            return {**data, "status": "paid_off" if closed else "open"}
        return data


class Question(Entry):
    id: str
    question: str = ""
    answer: str = ""
    resolved_on_page: int | None = None

    @property
    def is_open(self) -> bool:
        return self.resolved_on_page is None


class Memory(Entry):
    after_page: int = 0
    confidence: int = 0
    summary: str = ""
    characters: list[Character] = []
    glossary: list[Term] = []
    threads: list[Thread] = []
    questions: list[Question] = []
    changes: list[str] = []

    def dump(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)


class Patch(BaseModel):
    confidence: int | None = None
    summary: str = ""
    characters: list[Character] = []
    glossary: list[Term] = []
    threads: list[Thread] = []
    questions: list[Question] = []
    changes: list[str] = []
    speakers: dict[str, str | None] = {}


class ViewLevel(NamedTuple):
    whole_glossary: bool
    glossary_notes: bool
    description_chars: int
    thread_note_chars: int
    open_questions: int


VIEW_LEVELS = (
    ViewLevel(True, True, 300, 200, 20),
    ViewLevel(True, False, 150, 120, 12),
    ViewLevel(False, False, 150, 120, 12),
    ViewLevel(False, False, 100, 60, 6),
    ViewLevel(False, False, 60, 0, 0),
    ViewLevel(False, False, 0, 0, 0),
)
CUT_NOTE = "(the rest of the memory is cut to fit the prompt)"


def valid_items[E: BaseModel](model: type[E], items: Any) -> list[E]:
    if not isinstance(items, list):
        return []
    valid = []
    for item in items:
        try:
            valid.append(model.model_validate(item))
        except ValidationError:
            continue
    return valid


def as_int(value: Any) -> int | None:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def parse_patch(data: Any) -> Patch:
    if not isinstance(data, dict):
        raise BadOutput("memory patch is not a JSON object")
    speakers = data.get("speakers")
    changes = data.get("changes")
    return Patch(
        confidence=as_int(data.get("confidence")),
        summary=str(data.get("summary") or ""),
        characters=valid_items(Character, data.get("characters")),
        glossary=valid_items(Term, data.get("glossary")),
        threads=valid_items(Thread, data.get("threads")),
        questions=valid_items(Question, data.get("questions")),
        changes=[str(c) for c in changes if c] if isinstance(changes, list) else [],
        speakers={str(k): str(v) if v else None for k, v in speakers.items()}
        if isinstance(speakers, dict)
        else {},
    )


def filled_fields(entry: BaseModel) -> dict[str, Any]:
    return {
        k: v for k, v in entry.model_dump(exclude_unset=True).items() if v not in ("", None, [])
    }


def overlay[E: BaseModel](old: E, new: E) -> E:
    return old.model_copy(update=filled_fields(new))


def upsert[E: BaseModel](
    entries: list[E],
    updates: list[E],
    key: Callable[[E], str],
    combine: Callable[[E, E], E] = overlay,
) -> list[E]:
    merged = {key(e): e for e in entries}
    for update in updates:
        old = merged.get(key(update))
        merged[key(update)] = combine(old, update) if old else update
    return list(merged.values())


def compact(text: str) -> str:
    return "".join(text.split())


def term_key(term: Term) -> str:
    return compact(term.source)


def entry_id(entry: Character | Thread | Question) -> str:
    return entry.id


def with_known_ids(known: list[Character], updates: list[Character]) -> list[Character]:
    ids = {c.id for c in known}
    by_name = {c.name.strip().lower(): c.id for c in known if c.name}
    return [
        c.model_copy(update={"id": by_name[c.name.strip().lower()]})
        if c.id not in ids and c.name.strip().lower() in by_name
        else c
        for c in updates
    ]


def capped_character(c: Character) -> Character:
    return c.model_copy(
        update={
            "description": clip(c.description, DESCRIPTION_CHARS),
            "voice": clip(c.voice, VOICE_CHARS),
        }
    )


def capped_term(t: Term) -> Term:
    return t.model_copy(update={"note": clip(t.note, NOTE_CHARS)})


def capped_thread(t: Thread) -> Thread:
    return t.model_copy(update={"note": clip(t.note, NOTE_CHARS)})


def resolved_question(q: Question, page: int) -> Question:
    resolved_on = q.resolved_on_page if q.resolved_on_page is not None else page
    return q.model_copy(
        update={
            "question": clip(q.question, NOTE_CHARS),
            "answer": clip(q.answer, NOTE_CHARS),
            "resolved_on_page": resolved_on if q.answer else q.resolved_on_page,
        }
    )


def merge_thread(old: Thread, new: Thread) -> Thread:
    merged = overlay(old, new)
    return merged.model_copy(update={"pages": sorted(set(old.pages) | set(new.pages))})


def apply_patch(memory: Memory, patch: Patch, page: int) -> Memory:
    characters = with_known_ids(memory.characters, [capped_character(c) for c in patch.characters])
    confidence = memory.confidence if patch.confidence is None else patch.confidence
    return Memory(
        after_page=page,
        confidence=max(0, min(100, confidence)),
        summary=clip(patch.summary or memory.summary, SUMMARY_CHARS),
        characters=upsert(memory.characters, characters, entry_id),
        glossary=upsert(memory.glossary, [capped_term(t) for t in patch.glossary], term_key),
        threads=upsert(
            memory.threads, [capped_thread(t) for t in patch.threads], entry_id, merge_thread
        ),
        questions=upsert(
            memory.questions, [resolved_question(q, page) for q in patch.questions], entry_id
        ),
        changes=[clip(c, NOTE_CHARS) for c in patch.changes[:MAX_CHANGES]],
    )


def carry_over(memory: Memory) -> Memory:
    return Memory(
        after_page=0,
        confidence=memory.confidence,
        summary=memory.summary,
        characters=[c.model_copy(update={"first_seen_page": None}) for c in memory.characters],
        glossary=memory.glossary,
        threads=[t.model_copy(update={"pages": []}) for t in memory.threads if t.status == "open"],
        questions=[q for q in memory.questions if q.is_open],
        changes=[],
    )


def page_list(pages: list[int]) -> str:
    return ", ".join(f"p{p}" for p in pages) or "earlier chapter"


def story_lines(memory: Memory, level: ViewLevel) -> list[str]:
    lines = [
        f"Summary: {memory.summary or '(nothing yet)'}",
        "Characters (id | name | who | voice):",
    ]
    lines += [
        f"- {c.id} | {c.name} | {clip(c.description, level.description_chars)} | "
        f"{clip(c.voice, level.description_chars)}"
        for c in memory.characters
    ]
    return lines


def open_lines(memory: Memory, level: ViewLevel) -> list[str]:
    open_threads = [t for t in memory.threads if t.status == "open"]
    lines = ["Open threads (id | pages | note):"]
    lines += [
        f"- {t.id} | {page_list(t.pages)} | {clip(t.note, level.thread_note_chars)}"
        for t in open_threads
    ]
    paid_off = [t.id for t in memory.threads if t.status != "open"]
    if paid_off:
        lines.append("Paid-off threads: " + ", ".join(paid_off))
    open_questions = [q for q in memory.questions if q.is_open]
    shown = open_questions[-level.open_questions :] if level.open_questions else []
    lines.append(f"Open questions ({len(shown)} most recent of {len(open_questions)}):")
    lines += [f"- {q.id}: {q.question}" for q in shown]
    return lines


def term_line(term: Term, notes: bool) -> str:
    return f"- {term.source} -> {term.target}" + (f" ({term.note})" if notes and term.note else "")


def partial_glossary_title(hidden: int, total: int) -> str:
    return f"Glossary (source -> target; terms on this page first, {hidden} of {total} not shown):"


def glossary_lines(glossary: list[Term], level: ViewLevel, page_text: str, room: int) -> list[str]:
    lines = [term_line(t, level.glossary_notes) for t in glossary]
    if level.whole_glossary:
        return ["Glossary (source -> target):", *lines]
    page = compact(page_text)
    kept = {i for i, t in enumerate(glossary) if term_key(t) and term_key(t) in page}
    used = len(partial_glossary_title(len(glossary), len(glossary))) + 1
    used += sum(len(lines[i]) + 1 for i in kept)
    for i, line in enumerate(lines):
        if i not in kept and used + len(line) + 1 <= room:
            kept.add(i)
            used += len(line) + 1
    title = partial_glossary_title(len(glossary) - len(kept), len(glossary))
    return [title, *(lines[i] for i in sorted(kept))]


def render_view(memory: Memory, level: ViewLevel, budget: int, page_text: str) -> str:
    story = story_lines(memory, level)
    rest = open_lines(memory, level)
    room = budget - len("\n".join(story + rest))
    glossary = glossary_lines(memory.glossary, level, page_text, room)
    return "\n".join(story + glossary + rest)


def cut_to_budget(view: str, budget: int) -> str:
    kept: list[str] = []
    used = len(CUT_NOTE)
    for line in view.split("\n"):
        if used + len(line) + 1 > budget:
            break
        kept.append(line)
        used += len(line) + 1
    return "\n".join([*kept, CUT_NOTE])


def memory_view(memory: Memory, budget: int = settings.memory_chars, page_text: str = "") -> str:
    view = ""
    for level in VIEW_LEVELS:
        view = render_view(memory, level, budget, page_text)
        if len(view) <= budget:
            return view
    return cut_to_budget(view, budget)


def box_text(boxes: list[dict[str, Any]]) -> str:
    return " ".join(str(b.get("text") or "") for b in boxes)


def patch_prompt(memory: Memory, page: int, boxes: list[dict[str, Any]], lang: str) -> str:
    seeded = memory.after_page == 0 and bool(memory.characters or memory.glossary)
    title = SEEDED_TITLE if seeded else FIRST_PAGE_TITLE
    return MEMORY_PROMPT.format(
        lang=lang,
        memory_title=title.format(page=page),
        memory=memory_view(memory, page_text=box_text(boxes)),
        page=page,
        boxes="\n".join(f"- {b['id']} | {b['text']!r}" for b in boxes) or "(no text)",
    )


def image_part(image: bytes, mime: str) -> dict[str, Any]:
    url = f"data:{mime};base64,{base64.b64encode(image).decode()}"
    return {"type": "image_url", "image_url": {"url": url}}


async def complete_json(
    content: list[dict[str, Any]],
    model: str,
    max_tokens: int = PATCH_MAX_TOKENS,
    on_progress: Progress = no_progress,
    effort: str | None = None,
) -> tuple[Any, str, dict[str, Any]]:
    thinking = effort is not None
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "extra_body": {"chat_template_kwargs": {"thinking": thinking, "enable_thinking": thinking}},
        "messages": [{"role": "user", "content": content}],
    }
    optional: dict[str, Any] = {
        "response_format": {"type": "json_object"},
        "reasoning_effort": effort or "none",
    }
    text, usage = await stream_with_optional(kwargs, optional, on_progress)
    try:
        return json.loads(strip_fence(text)), text, usage
    except json.JSONDecodeError as e:
        if int(usage.get("completion_tokens") or 0) >= max_tokens:
            raise BadOutput(f"answer cut off at max_tokens={max_tokens}") from e
        raise BadOutput(f"invalid JSON after {len(text)} chars: {e}") from e


class MemoryUpdate(NamedTuple):
    memory: Memory
    speakers: dict[str, str | None]
    patch_chars: int
    usage: dict[str, Any]


async def update_memory(
    memory: Memory,
    page: int,
    image: bytes,
    mime: str,
    boxes: list[dict[str, Any]],
    model: str = settings.model,
    lang: str = settings.lang,
    effort: str | None = None,
) -> MemoryUpdate:
    prompt = patch_prompt(memory, page, boxes, lang)
    data, text, usage = await complete_json(
        [image_part(image, mime), {"type": "text", "text": prompt}], model, effort=effort
    )
    patch = parse_patch(data)
    return MemoryUpdate(apply_patch(memory, patch, page), patch.speakers, len(text), usage)
