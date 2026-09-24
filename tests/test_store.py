from pathlib import Path
from typing import Any

import pytest

from fukidashi import store


@pytest.fixture(autouse=True)
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name in ("PAGES", "RESULTS", "VOLUMES", "RENDERED"):
        monkeypatch.setattr(store, name, tmp_path / name.lower())
    store.ensure_dirs()
    return tmp_path


def save_result(page: str, characters: list[dict[str, Any]]) -> None:
    store.write_json(store.result_path(page), {"bubbles": [], "characters": characters})


def test_volume_characters_merge_in_page_order() -> None:
    store.save_volume("v", ["p1", "p2", "p3"])
    save_result("p1", [{"name": "Aki", "description": "a student"}])
    save_result("p3", [{"name": "Aki", "description": "a student, Ren's sister"}])
    save_result("p2", [{"name": "Ren", "description": "Aki's brother"}])
    assert store.volume_characters("v") == {
        "Aki": "a student, Ren's sister",
        "Ren": "Aki's brother",
    }


def test_volume_characters_replace_a_label_with_the_revealed_name() -> None:
    store.save_volume("v", ["p1", "p2"])
    save_result("p1", [{"name": "Girl in red", "description": "red coat"}])
    save_result("p2", [{"name": "Aki", "description": "red coat, a student", "was": "Girl in red"}])
    assert store.volume_characters("v") == {"Aki": "red coat, a student"}


def test_volume_characters_skip_pages_without_results() -> None:
    store.save_volume("v", ["p1", "p2"])
    save_result("p2", [{"name": "Ren", "description": "x"}])
    assert store.volume_characters("v") == {"Ren": "x"}
    assert store.volume_characters("missing") == {}
