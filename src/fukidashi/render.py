from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont

from fukidashi.detect import clamp

FONT = Path(__file__).parent / "static" / "fonts" / "ComicNeue-Bold.ttf"
INK = 128
PAPER = 200
OUTLINE_MARGIN = 3
INK_MARGIN = 2
INPAINT_RADIUS = 3
MIN_FONT = 9
MAX_FONT = 60
LINE_SPACING = 1.1
EXPAND = 1.0
CENTER = -1 / 3
MIN_FILL = 0.2
MAX_FILL = 3.0

Mask = NDArray[np.uint8]
Rect = tuple[int, int, int, int]


def scale(rect: Rect, ratio: float, width: int, height: int) -> Rect:
    x1, y1, x2, y2 = rect
    dx, dy = int((x2 - x1) * ratio), int((y2 - y1) * ratio)
    return (
        clamp(x1 - dx, width),
        clamp(y1 - dy, height),
        clamp(x2 + dx, width),
        clamp(y2 + dy, height),
    )


def disk(radius: int) -> Mask:
    size = 2 * radius + 1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size)).astype(np.uint8)


def bubble_interior(crop: Mask, box: Rect) -> Mask | None:
    paper = (crop > PAPER).astype(np.uint8)
    _, labels, stats, _ = cv2.connectedComponentsWithStats(paper)
    height, width = crop.shape
    cx1, cy1, cx2, cy2 = scale(box, CENTER, width, height)
    touching = set(np.unique(labels[cy1:cy2, cx1:cx2]).tolist()) - {0}
    if not touching:
        return None
    label = max(touching, key=lambda i: int(stats[i, cv2.CC_STAT_AREA]))
    component = (labels == label).astype(np.uint8)
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(paper)
    cv2.drawContours(filled, contours, -1, 1, cv2.FILLED)
    x1, y1, x2, y2 = box
    area = (x2 - x1) * (y2 - y1)
    if not MIN_FILL * area <= int(filled.sum()) <= MAX_FILL * area:
        return None
    return filled


def run_through(line: NDArray[np.bool_], at: int) -> tuple[int, int]:
    gaps = np.flatnonzero(~line)
    start = gaps[gaps < at].max(initial=-1) + 1
    stop = gaps[gaps > at].min(initial=len(line))
    return int(start), int(stop)


def inscribed_rect(mask: Mask, px: int, py: int) -> Rect:
    paper = mask.astype(bool)
    ys, xs = np.nonzero(paper)
    if len(ys) == 0:
        return (px, py, px, py)
    nearest = int(((ys - py) ** 2 + (xs - px) ** 2).argmin())
    px, py = int(xs[nearest]), int(ys[nearest])
    cols = np.arange(paper.shape[1])
    left = np.where(~paper[:, : px + 1], cols[: px + 1], -1).max(axis=1) + 1
    right = np.where(~paper[:, px:], cols[px:], len(cols)).min(axis=1)
    first, stop = run_through(paper[:, px], py)
    best, best_area = (px, py, px, py), 0
    for top in range(first, py + 1):
        lefts = np.maximum.accumulate(left[top:stop])
        rights = np.minimum.accumulate(right[top:stop])
        area = (rights - lefts) * np.arange(1, stop - top + 1)
        area[: py - top] = 0
        i = int(area.argmax())
        if area[i] > best_area:
            best, best_area = (int(lefts[i]), top, int(rights[i]), top + i + 1), int(area[i])
    return best


def place(gray: Mask, inside: Mask, bbox: Rect) -> Rect:
    height, width = gray.shape
    x1, y1, x2, y2 = scale(bbox, EXPAND, width, height)
    box = (bbox[0] - x1, bbox[1] - y1, bbox[2] - x1, bbox[3] - y1)
    interior = bubble_interior(gray[y1:y2, x1:x2], box)
    if interior is None:
        interior = np.zeros((y2 - y1, x2 - x1), np.uint8)
        interior[box[1] : box[3], box[0] : box[2]] = 1
    interior = cv2.erode(interior, disk(OUTLINE_MARGIN)).astype(np.uint8)
    inside[y1:y2, x1:x2] |= interior
    rect = inscribed_rect(interior, (box[0] + box[2]) // 2, (box[1] + box[3]) // 2)
    return (x1 + rect[0], y1 + rect[1], x1 + rect[2], y1 + rect[3])


def ink_mask(gray: Mask, inside: Mask) -> Mask:
    ink = cv2.dilate((gray < INK).astype(np.uint8), disk(INK_MARGIN)).astype(np.uint8)
    return ink & inside


def wrap(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and font.getlength(candidate) > width:
                lines.append(line)
                line = word
            else:
                line = candidate
        if line:
            lines.append(line)
    return lines


def line_height(font: ImageFont.FreeTypeFont) -> int:
    ascent, descent = font.getmetrics()
    return int((ascent + descent) * LINE_SPACING)


def fit(text: str, width: int, height: int) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    for size in range(max(MIN_FONT, min(MAX_FONT, height)), MIN_FONT - 1, -1):
        font = ImageFont.truetype(str(FONT), size)
        lines = wrap(text, font, width)
        fits_width = all(font.getlength(line) <= width for line in lines)
        if fits_width and len(lines) * line_height(font) <= height:
            break
    return font, lines


def draw_text(draw: ImageDraw.ImageDraw, text: str, rect: Rect) -> None:
    x1, y1, x2, y2 = rect
    width, height = x2 - x1, y2 - y1
    if width <= 0 or height <= 0:
        return
    font, lines = fit(text, width, height)
    step = line_height(font)
    y = y1 + (height - step * len(lines)) / 2
    for line in lines:
        draw.text((x1 + (width - font.getlength(line)) / 2, y), line, font=font, fill="black")
        y += step


def render(image: Image.Image, bubbles: list[dict[str, Any]]) -> Image.Image:
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.uint8)
    todo = [b for b in bubbles if b["kind"] != "sfx" and b["translation"].strip()]
    inside = np.zeros_like(gray)
    targets = [place(gray, inside, tuple(b["bbox"])) for b in todo]
    cleaned = cv2.inpaint(rgb, ink_mask(gray, inside), INPAINT_RADIUS, cv2.INPAINT_TELEA)
    out = Image.fromarray(cleaned)
    draw = ImageDraw.Draw(out)
    for bubble, target in zip(todo, targets, strict=True):
        draw_text(draw, bubble["translation"], target)
    return out
