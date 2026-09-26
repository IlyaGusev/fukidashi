import json
import re
from pathlib import Path
from typing import Any

import pytest

from fukidashi import detect
from fukidashi.book import BookOptions, BookPage, translate_book
from fukidashi.memory import Memory, Term
from fukidashi.settings import settings

PAGES = 45
BOX_ID = re.compile(r"^- (p\d+b\d+) \|", re.MULTILINE)
PAGE_NUMBER = re.compile(r"Page (\d+) is attached")


def book(pages: int = PAGES) -> list[BookPage]:
    return [
        BookPage(
            index=n,
            image=b"img",
            mime="image/jpeg",
            boxes=[{"id": f"p{n}b{i}", "text": f"せりふ{n}-{i}"} for i in (1, 2)],
        )
        for n in range(1, pages + 1)
    ]


class FakeModel:
    def __init__(
        self,
        broken_pages: frozenset[int] = frozenset(),
        broken_translations: frozenset[int] = frozenset(),
    ) -> None:
        self.broken_pages = broken_pages
        self.broken_translations = broken_translations
        self.memory_calls: list[int] = []
        self.translate_calls = 0
        self.prompts: list[str] = []
        self.sent: list[dict[str, Any]] = []

    async def __call__(
        self, kwargs: dict[str, Any], on_progress: Any
    ) -> tuple[str, dict[str, Any]]:
        prompt = kwargs["messages"][0]["content"][-1]["text"]
        self.prompts.append(prompt)
        self.sent.append(kwargs)
        page_match = PAGE_NUMBER.search(prompt)
        if page_match:
            page = int(page_match.group(1))
            self.memory_calls.append(page)
            if page in self.broken_pages:
                return '{"glossary": [', {"completion_tokens": 10}
            return json.dumps(self.patch(page, BOX_ID.findall(prompt))), {"completion_tokens": 50}
        self.translate_calls += 1
        ids = BOX_ID.findall(prompt)
        if any(i.startswith(f"p{n}b") for n in self.broken_translations for i in ids):
            return '{"translations": [', {"completion_tokens": 10}
        translations = [{"id": i, "translation": f"line {i}"} for i in BOX_ID.findall(prompt)]
        return json.dumps({"translations": translations}), {"completion_tokens": 20}

    def patch(self, page: int, box_ids: list[str]) -> dict[str, Any]:
        return {
            "confidence": min(100, 20 + page * 2),
            "summary": "the story " * 80,
            "characters": [{"id": f"c_{page % 4}", "description": f"seen on p{page} " * 50}],
            "glossary": [
                {"source": f"語{page}_{i}", "target": f"word {page}.{i}", "note": "n " * 80}
                for i in range(4)
            ],
            "threads": [{"id": f"t_{page}", "note": "thread " * 40, "pages": [page]}],
            "questions": [{"id": f"q_{page}", "question": "why " * 40}],
            "changes": [f"learned something on p{page}"],
            "speakers": {box_id: "Meru" for box_id in box_ids},
        }


@pytest.fixture
def model(monkeypatch: pytest.MonkeyPatch) -> Any:
    def install(
        broken_pages: frozenset[int] = frozenset(),
        broken_translations: frozenset[int] = frozenset(),
    ) -> FakeModel:
        fake = FakeModel(broken_pages, broken_translations)
        monkeypatch.setattr(detect, "stream_completion", fake)
        return fake

    return install


async def test_memory_updates_on_every_page_of_a_long_book(model: Any, tmp_path: Path) -> None:
    model()
    pages = book()
    result = await translate_book(pages, tmp_path / "ck.json", log=lambda line: None, backoff=0)
    stats = result["stats"]
    assert [s["page"] for s in stats] == list(range(1, PAGES + 1))
    assert not any(s["memoryFailed"] or s["translateFailed"] for s in stats)
    assert max(s["viewChars"] for s in stats) <= settings.memory_chars
    assert stats[-1]["glossary"] == 4 * PAGES
    assert pages[-1]["boxes"][0]["speaker"] == "Meru"
    assert pages[-1]["boxes"][0]["translation"] == f"line p{PAGES}b1"


async def test_failed_page_is_recorded_and_the_next_page_moves_on(
    model: Any, tmp_path: Path
) -> None:
    fake = model(frozenset({2}))
    result = await translate_book(book(4), tmp_path / "ck.json", log=lambda line: None, backoff=0)
    stats = result["stats"]
    assert [s["memoryFailed"] for s in stats] == [False, True, False, False]
    assert fake.memory_calls.count(2) == settings.attempts
    assert "failed" in result["snapshots"][1]["changes"][0]
    assert result["snapshots"][2]["afterPage"] == 3


async def test_rerun_resumes_from_the_checkpoint(model: Any, tmp_path: Path) -> None:
    model()
    checkpoint = tmp_path / "ck.json"
    await translate_book(book(3), checkpoint, log=lambda line: None, backoff=0)
    fake = model()
    pages = book(5)
    await translate_book(pages, checkpoint, log=lambda line: None, backoff=0)
    assert fake.memory_calls == [4, 5]
    assert pages[0]["boxes"][0]["firstPassTranslation"] == "line p1b1"


async def test_every_prompt_shows_the_pages_terms_from_a_large_seed(
    model: Any, tmp_path: Path
) -> None:
    fake = model()
    seed = Memory(glossary=[Term(source=f"名{i:04d}", target=f"name {i}") for i in range(2000)])
    page = BookPage(
        index=1, image=b"img", mime="image/jpeg", boxes=[{"id": "p1b1", "text": "名1999"}]
    )
    result = await translate_book(
        [page], tmp_path / "ck.json", seed=seed, log=lambda line: None, backoff=0
    )
    assert len(fake.prompts) == 2
    assert all("- 名1999 -> name 1999" in prompt for prompt in fake.prompts)
    assert result["stats"][0]["viewChars"] <= settings.memory_chars


async def test_without_memory_no_page_is_read_or_marked_failed(model: Any, tmp_path: Path) -> None:
    fake = model()
    result = await translate_book(
        book(3),
        tmp_path / "ck.json",
        log=lambda line: None,
        backoff=0,
        options=BookOptions(memory=False),
    )
    assert fake.memory_calls == []
    assert not any(s["memoryFailed"] for s in result["stats"])
    assert [s["glossary"] for s in result["stats"]] == [0, 0, 0]
    assert fake.translate_calls == 3


async def test_recent_pages_show_the_previous_lines_and_their_translations(
    model: Any, tmp_path: Path
) -> None:
    fake = model()
    options = BookOptions(recent_pages=1, second_pass=False)
    await translate_book(
        book(3), tmp_path / "ck.json", log=lambda line: None, backoff=0, options=options
    )
    first, second, third = [p for p in fake.prompts if "Translate the text boxes" in p]
    assert "Lines of the previous pages" not in first
    assert "- p1b1 | Meru | 'せりふ1-1' | 'line p1b1'" in second
    assert "p1b1" not in third
    assert "- p2b2 | Meru | 'せりふ2-2' | 'line p2b2'" in third


async def test_second_pass_runs_only_when_asked(model: Any, tmp_path: Path) -> None:
    fake = model()
    await translate_book(book(3), tmp_path / "off.json", log=lambda line: None, backoff=0)
    assert fake.translate_calls == 3
    options = BookOptions(second_pass=True)
    result = await translate_book(
        book(3), tmp_path / "on.json", log=lambda line: None, backoff=0, options=options
    )
    assert fake.translate_calls == 3 + 6
    assert result["revised"] == 0


async def test_memory_can_use_its_own_model_and_effort(model: Any, tmp_path: Path) -> None:
    fake = model()
    options = BookOptions(second_pass=False, memory_model="cheap", memory_effort="low")
    await translate_book(
        book(2), tmp_path / "ck.json", "strong", log=lambda line: None, backoff=0, options=options
    )
    calls = [
        (k["model"], k["reasoning_effort"], "Translate the text boxes" in p)
        for k, p in zip(fake.sent, fake.prompts, strict=True)
    ]
    assert calls == [
        ("cheap", "low", False),
        ("strong", "none", True),
        ("cheap", "low", False),
        ("strong", "none", True),
    ]


async def test_rerun_translates_a_failed_page_again_with_its_own_memory(
    model: Any, tmp_path: Path
) -> None:
    checkpoint = tmp_path / "ck.json"
    options = BookOptions(second_pass=False)
    model(broken_translations=frozenset({2}))
    first = await translate_book(
        book(3), checkpoint, log=lambda line: None, backoff=0, options=options
    )
    assert [s["translateFailed"] for s in first["stats"]] == [False, True, False]
    fake = model()
    pages = book(3)
    second = await translate_book(
        pages, checkpoint, log=lambda line: None, backoff=0, options=options
    )
    assert fake.memory_calls == []
    assert fake.translate_calls == 1
    assert "Page 2" not in fake.prompts[0]
    assert "- 語2_0 -> word 2.0" in fake.prompts[0]
    assert "- 語3_0 ->" not in fake.prompts[0]
    assert [s["translateFailed"] for s in second["stats"]] == [False, False, False]
    assert pages[1]["boxes"][0]["translation"] == "line p2b1"
