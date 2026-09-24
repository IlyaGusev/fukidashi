import json
from pathlib import Path

from fukidashi.store import INBOX, Store

RESULT = {
    "bubbles": [{"text": "a"}],
    "size": [1, 1],
    "model": "m",
    "thinking": False,
    "lang": "English",
}


def test_legacy_folders_are_imported_once(tmp_path: Path) -> None:
    pages = tmp_path / "pages"
    pages.mkdir()
    for name in ("aaa__1.png", "bbb__2.png", "ccc__loose.png"):
        (pages / name).write_bytes(name.encode())
    (tmp_path / "volumes").mkdir()
    (tmp_path / "volumes" / "vol.json").write_text(
        json.dumps({"name": "My vol", "pages": ["aaa__1.png", "bbb__2.png"]})
    )
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "bbb__2.png.json").write_text(json.dumps({**RESULT, "usage": {}}))

    store = Store(tmp_path)
    volumes = {v["title"]: v for v in store.list_volumes()}
    assert volumes["My vol"]["pages"] == 2
    assert volumes["My vol"]["translated"] == 1
    assert volumes[INBOX]["pages"] == 1
    second = store.get_volume(volumes["My vol"]["id"])
    assert second is not None
    translated = second["pages"][1]
    assert translated["file"] == "bbb__2.png"
    assert store.get_translation(translated["current"]) is not None
    assert [v["title"] for v in Store(tmp_path).list_volumes()] == [INBOX, "My vol"]


def test_reorder_and_upload_dedup(tmp_path: Path) -> None:
    store = Store(tmp_path)
    volume = store.create_volume("v")["id"]
    store.add_pages(volume, [(b"1", "1.png", None), (b"2", "2.png", None), (b"1", "1.png", None)])
    first, second = store.volume_pages(volume)
    store.reorder_pages(volume, [second, first])
    assert store.volume_pages(volume) == [second, first]
    assert store.context_for(first) is None
    store.add_translation(second, RESULT)
    assert store.context_for(first) == ["a"]
