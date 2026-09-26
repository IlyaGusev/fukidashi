import json
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from PIL import Image

from fukidashi import detect, store

OPTIONS = {"model": "m", "thinking": False, "lang": "English"}
DETECTION = "Find every text container"


def png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (40, 60), "white").save(buffer, "PNG")
    return buffer.getvalue()


class FakeModel:
    def __init__(self) -> None:
        self.detections: list[str] = []
        self.memory_prompts: list[str] = []

    async def __call__(
        self, kwargs: dict[str, Any], on_progress: Any
    ) -> tuple[str, dict[str, Any]]:
        prompt = kwargs["messages"][0]["content"][-1]["text"]
        if DETECTION in prompt:
            self.detections.append(prompt)
            bubble = {
                "bbox": [1, 1, 20, 20],
                "kind": "speech",
                "text": "メル!",
                "translation": "Mel!",
            }
            return json.dumps({"bubbles": [bubble]}), {"completion_tokens": 20}
        self.memory_prompts.append(prompt)
        page = len(self.memory_prompts)
        patch = {
            "confidence": 50 + page,
            "glossary": [{"source": f"名{page}", "target": f"Name{page}"}],
            "speakers": {"b1": "Mel"},
        }
        return json.dumps(patch), {"completion_tokens": 30}


@pytest.fixture
def model(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeModel:
    for name in ("PAGES", "RESULTS", "VOLUMES", "RENDERED", "MEMORY"):
        monkeypatch.setattr(store, name, tmp_path / name.lower())
    store.ensure_dirs()
    fake = FakeModel()
    monkeypatch.setattr(detect, "stream_completion", fake)
    return fake


def volume_of(pages: int) -> list[str]:
    names = [store.save_page(png() + bytes([i]), f"p{i}.png", "image/png") for i in range(pages)]
    store.save_volume("Vol", names)
    return names


async def test_volume_pages_are_translated_with_the_notes_of_the_pages_before(
    model: FakeModel,
) -> None:
    p1, p2 = volume_of(2)
    first = await store.translate_page(p1, OPTIONS, None, volume="Vol")
    await store.translate_page(p2, OPTIONS, p1, volume="Vol")
    assert "Story memory" not in model.detections[0]
    assert "Story memory" in model.detections[1]
    assert "- 名1 -> Name1" in model.detections[1]
    assert "Page 2 is attached" in model.memory_prompts[1]
    assert first["bubbles"][0]["speaker"] == "Mel"
    assert first["memoryFailed"] is False
    memory = store.volume_memory("Vol", "m", "English")
    assert memory is not None
    assert [t.target for t in memory.glossary] == ["Name1", "Name2"]
    assert store.memory_before("Vol", p2, "m", "English").glossary[0].target == "Name1"


async def test_a_single_page_keeps_the_previous_page_context(model: FakeModel) -> None:
    p1, p2 = volume_of(2)
    await store.translate_page(p1, OPTIONS)
    await store.translate_page(p2, OPTIONS, p1)
    assert model.memory_prompts == []
    assert "Text from the previous page" in model.detections[1]
    assert store.volume_memory("Vol", "m", "English") is None


async def test_a_failed_memory_update_keeps_the_translation(
    model: FakeModel, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def detect_then_garbage(
        kwargs: dict[str, Any], on_progress: Any
    ) -> tuple[str, dict[str, Any]]:
        prompt = kwargs["messages"][0]["content"][-1]["text"]
        if DETECTION in prompt:
            return await model(kwargs, on_progress)
        return "not json", {"completion_tokens": 5}

    monkeypatch.setattr(detect, "stream_completion", detect_then_garbage)
    monkeypatch.setattr(store, "MEMORY_BACKOFF", 0)
    [p1] = volume_of(1)
    result = await store.translate_page(p1, OPTIONS, volume="Vol")
    assert result["bubbles"][0]["translation"] == "Mel!"
    assert result["memoryFailed"] is True
    memory = store.volume_memory("Vol", "m", "English")
    assert memory is not None
    assert "failed" in memory.changes[0]
