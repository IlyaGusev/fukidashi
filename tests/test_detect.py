from typing import Any

import httpx2 as httpx
import openai
import pytest

from fukidashi import detect
from fukidashi.detect import (
    PROMPTS,
    BadOutput,
    no_progress,
    parse_answer,
    stream_with_optional,
)


def bad_request(message: str) -> openai.BadRequestError:
    response = httpx.Response(400, request=httpx.Request("POST", "http://api"))
    return openai.BadRequestError(message, response=response, body=None)


class FakeServer:
    def __init__(self, rejects: set[str], named: bool = True) -> None:
        self.rejects = rejects
        self.named = named
        self.calls: list[dict[str, Any]] = []

    async def __call__(
        self, kwargs: dict[str, Any], on_progress: Any
    ) -> tuple[str, dict[str, Any]]:
        self.calls.append(kwargs)
        rejected = sorted(self.rejects & kwargs.keys())
        if rejected:
            raise bad_request(f"unknown field {rejected[0]}" if self.named else "bad request")
        return "ok", {}


@pytest.fixture
def server(monkeypatch: pytest.MonkeyPatch) -> Any:
    def install(rejects: set[str], named: bool = True) -> FakeServer:
        fake = FakeServer(rejects, named)
        monkeypatch.setattr(detect, "stream_completion", fake)
        return fake

    return install


async def test_keeps_optional_fields_the_server_accepts(server: Any) -> None:
    fake = server(set())
    await stream_with_optional({"model": "m"}, {"a": 1, "b": 2}, no_progress)
    assert fake.calls == [{"model": "m", "a": 1, "b": 2}]


async def test_drops_only_the_named_rejected_field(server: Any) -> None:
    fake = server({"b"})
    await stream_with_optional({"model": "m"}, {"a": 1, "b": 2}, no_progress)
    assert fake.calls[-1] == {"model": "m", "a": 1}


async def test_drops_all_optional_fields_when_error_names_none(server: Any) -> None:
    fake = server({"b"}, named=False)
    await stream_with_optional({"model": "m"}, {"a": 1, "b": 2}, no_progress)
    assert fake.calls[-1] == {"model": "m"}


async def test_raises_when_the_required_fields_are_rejected(server: Any) -> None:
    server({"model"})
    with pytest.raises(openai.BadRequestError):
        await stream_with_optional({"model": "m"}, {"a": 1}, no_progress)


def test_parse_answer_reads_bubbles_and_characters() -> None:
    text = """```json
{"bubbles": [{"bbox": [0, 0, 10, 10], "text": "a", "translation": "b"}],
 "characters": [{"name": " Aki ", "description": "the hero", "was": "Girl in red"},
                {"name": "Ren", "description": "", "was": "Ren"}, {"name": ""}, "junk"]}
```"""
    result = parse_answer(text, 100, 100)
    assert result["bubbles"][0]["kind"] == "speech"
    assert result["characters"] == [
        {"name": "Aki", "description": "the hero", "was": "Girl in red"},
        {"name": "Ren", "description": ""},
    ]


def test_parse_answer_tolerates_missing_characters() -> None:
    assert parse_answer('{"bubbles": []}', 10, 10) == {"bubbles": [], "characters": []}


def test_parse_answer_requires_bubbles() -> None:
    with pytest.raises(BadOutput):
        parse_answer('{"characters": []}', 10, 10)


def render_prompt(**kwargs: Any) -> str:
    defaults: dict[str, Any] = {
        "w": 10,
        "h": 20,
        "lang": "English",
        "context": None,
        "characters": None,
    }
    return PROMPTS.get_template("detect.jinja").render({**defaults, **kwargs})


def test_prompt_without_context_has_no_context_sections() -> None:
    prompt = render_prompt()
    assert prompt.startswith("This is a page from a manga or comic (10x20 pixels).")
    assert "previous page" not in prompt
    assert "Known characters" not in prompt
    assert prompt.count("\n\n") == 1


def test_prompt_lists_context_and_characters() -> None:
    prompt = render_prompt(context=["こんにちは"], characters={"Aki": "the hero"})
    assert (
        "Text from the previous page, for consistent names, terms and tone:\n- こんにちは\n"
        in prompt
    )
    assert "Known characters in this volume so far:\n- Aki: the hero\n" in prompt
