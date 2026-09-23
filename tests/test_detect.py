from typing import Any

import httpx2 as httpx
import openai
import pytest

from fukidashi import detect
from fukidashi.detect import no_progress, stream_with_optional


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
