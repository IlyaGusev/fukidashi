import json
from typing import Any

import pytest

from fukidashi import detect
from fukidashi.detect import BadOutput
from fukidashi.memory import (
    DESCRIPTION_CHARS,
    MAX_CHANGES,
    Memory,
    apply_patch,
    carry_over,
    memory_view,
    parse_patch,
    update_memory,
)

BUDGET = 16000


def patched(memory: Memory, page: int, **fields: Any) -> Memory:
    return apply_patch(memory, parse_patch(fields), page)


def growing_patch(page: int) -> dict[str, Any]:
    return {
        "confidence": 90,
        "summary": "story " * 200,
        "characters": [
            {
                "id": f"c_{page % 5}",
                "name": f"Name {page % 5}",
                "description": f"on page {page} " * 40,
                "voice": "says things " * 30,
            }
        ],
        "glossary": [
            {"source": f"用語{page}_{i}", "target": f"term {page}.{i}", "note": "why " * 30}
            for i in range(3)
        ],
        "threads": [{"id": f"t_{page}", "note": "setup " * 50, "pages": [page]}],
        "questions": [{"id": f"q_{page}_{i}", "question": "who? " * 30} for i in range(2)],
        "changes": ["changed " * 50] * 6,
    }


class FakeModel:
    def __init__(self, answers: list[tuple[str, dict[str, Any]]]) -> None:
        self.answers = answers
        self.prompts: list[str] = []

    async def __call__(
        self, kwargs: dict[str, Any], on_progress: Any
    ) -> tuple[str, dict[str, Any]]:
        self.prompts.append(kwargs["messages"][0]["content"][-1]["text"])
        return self.answers.pop(0)


def test_glossary_entry_left_out_of_a_patch_is_kept() -> None:
    memory = patched(
        Memory(),
        1,
        glossary=[{"source": "メル", "target": "Meru"}, {"source": "薬屋", "target": "pharmacy"}],
    )
    memory = patched(memory, 2, glossary=[{"source": "カエル", "target": "frog"}])
    assert [t.target for t in memory.glossary] == ["Meru", "pharmacy", "frog"]


def test_patch_overwrites_only_the_fields_it_fills() -> None:
    first = {"id": "c_meru", "name": "Meru", "description": "child", "voice": "polite"}
    memory = patched(Memory(), 1, characters=[first])
    memory = patched(memory, 2, characters=[{"id": "c_meru", "description": "live-in helper"}])
    [meru] = memory.characters
    assert (meru.name, meru.description, meru.voice) == ("Meru", "live-in helper", "polite")


def test_new_id_for_a_known_name_updates_the_same_character() -> None:
    memory = patched(Memory(), 1, characters=[{"id": "c_meru", "name": "Meru", "voice": "shy"}])
    memory = patched(memory, 2, characters=[{"id": "c_meru2", "name": "meru", "voice": "loud"}])
    assert [(c.id, c.voice) for c in memory.characters] == [("c_meru", "loud")]


def test_character_without_id_gets_one_from_its_name() -> None:
    memory = patched(Memory(), 1, characters=[{"name": "The Pharmacist"}])
    assert memory.characters[0].id == "c_the_pharmacist"


def test_thread_pages_accumulate_and_status_survives_an_update_without_one() -> None:
    memory = patched(Memory(), 3, threads=[{"id": "t_wallet", "note": "lost", "pages": [3]}])
    memory = patched(memory, 9, threads=[{"id": "t_wallet", "status": "Paid off", "pages": [9]}])
    memory = patched(memory, 12, threads=[{"id": "t_wallet", "pages": [12]}])
    [wallet] = memory.threads
    assert (wallet.status, wallet.pages, wallet.note) == ("paid_off", [3, 9, 12], "lost")


def test_an_answer_resolves_the_question_on_the_current_page() -> None:
    memory = patched(Memory(), 5, questions=[{"id": "q7", "question": "What is the dish?"}])
    answer = {"id": "q7", "status": "resolvedOnPage", "answer": "curry rice"}
    memory = patched(memory, 31, questions=[answer])
    [dish] = memory.questions
    assert (dish.question, dish.answer, dish.resolved_on_page) == (
        "What is the dish?",
        answer["answer"],
        31,
    )
    assert not dish.is_open


def test_long_fields_and_change_lists_are_capped() -> None:
    memory = patched(Memory(), 1, **growing_patch(1))
    assert len(memory.characters[0].description) <= DESCRIPTION_CHARS
    assert len(memory.changes) == MAX_CHANGES


def test_malformed_items_are_skipped_not_fatal() -> None:
    patch = parse_patch(
        {
            "confidence": "85",
            "glossary": [{"target": "no source"}, "junk", {"source": "a", "target": "b"}],
            "characters": "not a list",
            "speakers": {"p1b1": "Meru", "p1b2": 0},
        }
    )
    assert patch.confidence == 85
    assert [t.source for t in patch.glossary] == ["a"]
    assert patch.characters == []
    assert patch.speakers == {"p1b1": "Meru", "p1b2": None}


def test_a_patch_that_is_not_an_object_is_bad_output() -> None:
    with pytest.raises(BadOutput):
        parse_patch([1, 2])


def test_view_stays_within_budget_for_a_sixty_page_book() -> None:
    memory = Memory()
    views = []
    for page in range(1, 61):
        memory = apply_patch(memory, parse_patch(growing_patch(page)), page)
        views.append(memory_view(memory, BUDGET))
    assert max(len(v) for v in views) <= BUDGET
    assert len(memory.glossary) == 180
    assert all(f"{t.source} -> {t.target}" in views[-1] for t in memory.glossary)


def test_view_keeps_this_pages_terms_when_the_glossary_outgrows_the_budget() -> None:
    memory = Memory()
    for page in range(1, 401):
        memory = apply_patch(memory, parse_patch(growing_patch(page)), page)
    view = memory_view(memory, BUDGET, page_text="用語400_2 と 用語250_1")
    assert len(memory.glossary) == 1200
    assert len(view) <= BUDGET
    assert "- 用語400_2 -> term 400.2" in view
    assert "- 用語250_1 -> term 250.1" in view
    assert "- 用語1_0 -> term 1.0" in view
    assert "- 用語399_0 ->" not in view
    assert " of 1200 not shown" in view


def test_carry_over_keeps_the_cast_and_drops_page_state() -> None:
    memory = patched(
        Memory(),
        40,
        confidence=95,
        characters=[{"id": "c_meru", "name": "Meru", "firstSeenPage": 1}],
        glossary=[{"source": "メル", "target": "Meru"}],
        threads=[
            {"id": "t_open", "pages": [3]},
            {"id": "t_done", "status": "paid_off", "pages": [5]},
        ],
        questions=[
            {"id": "q_open", "question": "Who?"},
            {"id": "q_done", "question": "What?", "answer": "curry"},
        ],
        changes=["something"],
    )
    seeded = carry_over(memory)
    assert (seeded.after_page, seeded.confidence, seeded.changes) == (0, 95, [])
    assert [(t.id, t.pages) for t in seeded.threads] == [("t_open", [])]
    assert [q.id for q in seeded.questions] == ["q_open"]
    assert seeded.characters[0].first_seen_page is None
    assert seeded.glossary == memory.glossary


async def test_update_memory_applies_the_patch_and_returns_speakers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    answer = json.dumps(
        {
            "confidence": 40,
            "glossary": [{"source": "メル", "target": "Meru"}],
            "speakers": {"p1b1": "Meru"},
        }
    )
    fake = FakeModel([(answer, {"completion_tokens": 30})])
    monkeypatch.setattr(detect, "stream_completion", fake)
    update = await update_memory(
        Memory(), 1, b"img", "image/jpeg", [{"id": "p1b1", "text": "メル"}]
    )
    assert update.memory.after_page == 1
    assert update.memory.glossary[0].target == "Meru"
    assert update.speakers == {"p1b1": "Meru"}
    assert "p1b1 | 'メル'" in fake.prompts[0]


async def test_memory_prompt_shows_the_pages_terms_from_a_large_glossary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeModel([("{}", {})])
    monkeypatch.setattr(detect, "stream_completion", fake)
    terms = [{"source": f"名{i:04d}", "target": f"name {i}"} for i in range(2000)]
    memory = patched(Memory(), 1, glossary=terms)
    await update_memory(memory, 2, b"img", "image/jpeg", [{"id": "p2b1", "text": "名1999だ"}])
    assert "- 名1999 -> name 1999" in fake.prompts[0]
    assert "- 名1998 ->" not in fake.prompts[0]


async def test_seeded_memory_is_labelled_as_carried_over(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeModel([("{}", {})])
    monkeypatch.setattr(detect, "stream_completion", fake)
    seed = carry_over(patched(Memory(), 40, glossary=[{"source": "メル", "target": "Meru"}]))
    await update_memory(seed, 1, b"img", "image/jpeg", [])
    assert "carried over from the previous chapters" in fake.prompts[0]
    assert "メル -> Meru" in fake.prompts[0]


async def test_answer_cut_off_at_max_tokens_says_so(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeModel([('{"glossary": [{"source": "a"', {"completion_tokens": 16000})])
    monkeypatch.setattr(detect, "stream_completion", fake)
    with pytest.raises(BadOutput, match="max_tokens"):
        await update_memory(Memory(), 1, b"img", "image/jpeg", [])


async def test_effort_turns_thinking_on_at_that_level(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: list[dict[str, Any]] = []

    async def fake(kwargs: dict[str, Any], on_progress: Any) -> tuple[str, dict[str, Any]]:
        sent.append(kwargs)
        return "{}", {}

    monkeypatch.setattr(detect, "stream_completion", fake)
    await update_memory(Memory(), 1, b"img", "image/jpeg", [], effort="low")
    await update_memory(Memory(), 1, b"img", "image/jpeg", [])
    assert [k["reasoning_effort"] for k in sent] == ["low", "none"]
    assert [k["extra_body"]["chat_template_kwargs"]["thinking"] for k in sent] == [True, False]
