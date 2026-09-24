import hashlib
import json
import mimetypes
import re
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from PIL import Image

from fukidashi.render import render

INBOX = "Inbox"
SCHEMA = """
CREATE TABLE IF NOT EXISTS volumes (
    id INTEGER PRIMARY KEY, title TEXT NOT NULL UNIQUE, created REAL NOT NULL);
CREATE TABLE IF NOT EXISTS pages (
    id INTEGER PRIMARY KEY, volume INTEGER NOT NULL REFERENCES volumes(id) ON DELETE CASCADE,
    position INTEGER NOT NULL, file TEXT NOT NULL,
    current INTEGER REFERENCES translations(id) ON DELETE SET NULL);
CREATE TABLE IF NOT EXISTS translations (
    id INTEGER PRIMARY KEY, page INTEGER NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    created REAL NOT NULL, model TEXT NOT NULL, thinking INTEGER NOT NULL, lang TEXT NOT NULL,
    bubbles TEXT NOT NULL, size TEXT NOT NULL, usage TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS pages_volume ON pages(volume, position);
CREATE INDEX IF NOT EXISTS translations_page ON translations(page);
"""
VOLUME_LIST = """
SELECT v.id, v.title, v.created,
    (SELECT count(*) FROM pages WHERE volume = v.id) AS pages,
    (SELECT count(*) FROM pages WHERE volume = v.id AND current IS NOT NULL) AS translated
FROM volumes v ORDER BY v.title
"""
PAGE_LIST = """
SELECT p.id, p.position, p.file, p.current,
    (SELECT count(*) FROM translations WHERE page = p.id) AS versions
FROM pages p WHERE p.volume = ? ORDER BY p.position
"""
VERSION_LIST = """
SELECT id, created, model, thinking, lang, json_array_length(bubbles) AS boxes,
    json_extract(usage, '$.total_tokens') AS tokens
FROM translations WHERE page = ? ORDER BY created DESC
"""
PREVIOUS_TEXT = """
SELECT t.bubbles FROM pages p
JOIN pages prev ON prev.volume = p.volume AND prev.position = (
    SELECT max(position) FROM pages WHERE volume = p.volume AND position < p.position)
JOIN translations t ON t.id = prev.current
WHERE p.id = ?
"""

Upload = tuple[bytes, str | None, str | None]


def safe(name: str) -> str:
    return re.sub(r"[^\w.-]+", "_", name.strip())[:60] or "untitled"


def write_atomic(path: Path, write: Callable[[Path], object]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    write(tmp)
    tmp.replace(path)


def file_name(data: bytes, filename: str | None, content_type: str | None) -> str:
    ext = Path(filename or "").suffix or mimetypes.guess_extension(content_type or "") or ".png"
    return f"{hashlib.sha1(data).hexdigest()[:12]}__{safe(Path(filename or 'page').stem)}{ext}"


def parse_translation(row: sqlite3.Row) -> dict[str, Any]:
    return {
        **dict(row),
        "thinking": bool(row["thinking"]),
        "bubbles": json.loads(row["bubbles"]),
        "size": json.loads(row["size"]),
        "usage": json.loads(row["usage"]),
    }


class Store:
    def __init__(self, data_dir: Path) -> None:
        self.pages_dir = data_dir / "pages"
        self.rendered_dir = data_dir / "rendered"
        for d in (self.pages_dir, self.rendered_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(
            data_dir / "fukidashi.db", isolation_level=None, check_same_thread=False
        )
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.execute("PRAGMA synchronous = NORMAL")
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)
        self._import_legacy(data_dir)

    def close(self) -> None:
        self.db.close()

    def list_volumes(self) -> list[dict[str, Any]]:
        if not self.db.execute("SELECT 1 FROM volumes LIMIT 1").fetchone():
            self.create_volume(INBOX)
        return [dict(r) for r in self.db.execute(VOLUME_LIST)]

    def create_volume(self, title: str) -> dict[str, Any]:
        volume = self.get_volume(self._insert_volume(title.strip()))
        assert volume is not None
        return volume

    def volume_by_title(self, title: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT id FROM volumes WHERE title = ?", (title,)).fetchone()
        return self.get_volume(row["id"]) if row else None

    def get_volume(self, volume: int) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM volumes WHERE id = ?", (volume,)).fetchone()
        if row is None:
            return None
        return {**dict(row), "pages": [dict(p) for p in self.db.execute(PAGE_LIST, (volume,))]}

    def rename_volume(self, volume: int, title: str) -> None:
        self.db.execute("UPDATE volumes SET title = ? WHERE id = ?", (title.strip(), volume))

    def delete_volume(self, volume: int) -> None:
        self.db.execute("DELETE FROM volumes WHERE id = ?", (volume,))

    def volume_pages(self, volume: int) -> list[int]:
        rows = self.db.execute("SELECT id FROM pages WHERE volume = ? ORDER BY position", (volume,))
        return [r["id"] for r in rows]

    def add_pages(self, volume: int, uploads: list[Upload]) -> None:
        files = []
        for data, filename, content_type in uploads:
            name = file_name(data, filename, content_type)
            path = self.pages_dir / name
            if not path.exists():
                path.write_bytes(data)
            files.append(name)
        self.db.execute("BEGIN")
        self._insert_pages(volume, files)
        self.db.execute("COMMIT")

    def _insert_pages(self, volume: int, files: list[str]) -> None:
        rows = self.db.execute("SELECT file, position FROM pages WHERE volume = ?", (volume,))
        existing = {r["file"]: r["position"] for r in rows}
        next_position = max(existing.values(), default=-1) + 1
        new = [f for f in dict.fromkeys(files) if f not in existing]
        self.db.executemany(
            "INSERT INTO pages (volume, position, file) VALUES (?, ?, ?)",
            [(volume, next_position + i, f) for i, f in enumerate(new)],
        )

    def get_page(self, page: int) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM pages WHERE id = ?", (page,)).fetchone()
        if row is None:
            return None
        versions = [
            {**dict(v), "thinking": bool(v["thinking"])}
            for v in self.db.execute(VERSION_LIST, (page,))
        ]
        return {**dict(row), "versions": versions}

    def page_path(self, page: int) -> Path:
        row = self.db.execute("SELECT file FROM pages WHERE id = ?", (page,)).fetchone()
        return self.pages_dir / str(row["file"])

    def reorder_pages(self, volume: int, order: list[int]) -> None:
        self.db.execute("BEGIN")
        self.db.executemany(
            "UPDATE pages SET position = ? WHERE id = ? AND volume = ?",
            [(i, page, volume) for i, page in enumerate(order)],
        )
        self.db.execute("COMMIT")

    def remove_page(self, page: int) -> None:
        self.db.execute("DELETE FROM pages WHERE id = ?", (page,))

    def context_for(self, page: int) -> list[str] | None:
        row = self.db.execute(PREVIOUS_TEXT, (page,)).fetchone()
        if row is None:
            return None
        return [b["text"] for b in json.loads(row["bubbles"])]

    def add_translation(self, page: int, result: dict[str, Any], created: float = 0) -> int:
        self.db.execute("BEGIN")
        cursor = self.db.execute(
            "INSERT INTO translations (page, created, model, thinking, lang, bubbles, size, usage) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                page,
                created or time.time(),
                result["model"],
                result["thinking"],
                result["lang"],
                json.dumps(result["bubbles"], ensure_ascii=False),
                json.dumps(result.get("size")),
                json.dumps(result.get("usage") or {}),
            ),
        )
        translation = cursor.lastrowid or 0
        self.db.execute("UPDATE pages SET current = ? WHERE id = ?", (translation, page))
        self.db.execute("COMMIT")
        return translation

    def get_translation(self, translation: int) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM translations WHERE id = ?", (translation,)).fetchone()
        return parse_translation(row) if row else None

    def set_current(self, page: int, translation: int) -> bool:
        cursor = self.db.execute(
            "UPDATE pages SET current = ? WHERE id = ? "
            "AND EXISTS (SELECT 1 FROM translations WHERE id = ? AND page = ?)",
            (translation, page, translation, page),
        )
        return cursor.rowcount == 1

    def render(self, translation: int) -> Path | None:
        found = self.get_translation(translation)
        if found is None:
            return None
        target = self.rendered_dir / f"{translation}.png"
        if not target.is_file():
            image = render(Image.open(self.page_path(found["page"])), found["bubbles"])
            write_atomic(target, lambda tmp: image.save(tmp, "PNG"))
        return target

    def _import_legacy(self, data_dir: Path) -> None:
        if self.db.execute("SELECT 1 FROM volumes LIMIT 1").fetchone():
            return
        volume_files = sorted((data_dir / "volumes").glob("*.json"))
        placed: set[str] = set()
        self.db.execute("BEGIN")
        for path in volume_files:
            legacy = json.loads(path.read_text())
            self._insert_pages(self._insert_volume(legacy["name"]), legacy["pages"])
            placed.update(legacy["pages"])
        loose = sorted(
            (p for p in self.pages_dir.iterdir() if p.name not in placed),
            key=lambda p: p.stat().st_mtime,
        )
        if loose:
            self._insert_pages(self._insert_volume(INBOX), [p.name for p in loose])
        self.db.execute("COMMIT")
        for row in self.db.execute("SELECT id, file FROM pages").fetchall():
            result_path = data_dir / "results" / f"{row['file']}.json"
            if result_path.is_file():
                result = json.loads(result_path.read_text())
                self.add_translation(row["id"], result, result_path.stat().st_mtime)

    def _insert_volume(self, title: str) -> int:
        cursor = self.db.execute(
            "INSERT INTO volumes (title, created) VALUES (?, ?)", (title, time.time())
        )
        return cursor.lastrowid or 0
