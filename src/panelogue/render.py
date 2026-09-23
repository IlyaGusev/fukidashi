from pathlib import Path
from typing import Any

import cv2
import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont

FONT = Path(__file__).parent / "static" / "fonts" / "ComicNeue-Bold.ttf"
INK = 128
PAPER = 200
OUTLINE_MARGIN = 3
INPAINT_RADIUS = 3
MIN_FONT = 9
MAX_FONT = 60
LINE_SPACING = 1.1
INSET = 0.12
EXPAND = 1.0
MIN_FILL = 0.2
MAX_FILL = 3.0
SKIPPED_KINDS = {"sfx"}

Mask = NDArray[np.uint8]
Rect = tuple[int, int, int, int]


def expand(rect: Rect, ratio: float, width: int, height: int) -> Rect:
    x1, y1, x2, y2 = rect
    dx, dy = int((x2 - x1) * ratio), int((y2 - y1) * ratio)
    return max(0, x1 - dx), max(0, y1 - dy), min(width, x2 + dx), min(height, y2 + dy)


def bubble_interior(gray: NDArray[np.uint8], rect: Rect) -> Mask | None:
    bx1, by1, bx2, by2 = rect
    area = (bx2 - bx1) * (by2 - by1)
    x1, y1, x2, y2 = expand(rect, EXPAND, gray.shape[1], gray.shape[0])
    crop = gray[y1:y2, x1:x2]
    paper = (crop > PAPER).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(paper)
    if count < 2:
        return None
    cx1, cy1, cx2, cy2 = inset((bx1 - x1, by1 - y1, bx2 - x1, by2 - y1), 1 / 3)
    center = labels[cy1:cy2, cx1:cx2]
    candidates = [i for i in range(1, count) if np.any(center == i)]
    if not candidates:
        return None
    label = max(candidates, key=lambda i: int(stats[i, cv2.CC_STAT_AREA]))
    component = (labels == label).astype(np.uint8)
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    filled = np.zeros_like(component)
    cv2.drawContours(filled, contours, -1, 1, cv2.FILLED)
    if not MIN_FILL * area <= int(filled.sum()) <= MAX_FILL * area:
        return None
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * OUTLINE_MARGIN + 1,) * 2)
    interior = np.zeros_like(gray)
    interior[y1:y2, x1:x2] = cv2.erode(filled, kernel)
    return interior


def inset(rect: Rect, ratio: float) -> Rect:
    x1, y1, x2, y2 = rect
    dx, dy = int((x2 - x1) * ratio), int((y2 - y1) * ratio)
    return x1 + dx, y1 + dy, x2 - dx, y2 - dy


def region_of(gray: NDArray[np.uint8], rect: Rect) -> tuple[Mask, Rect]:
    interior = bubble_interior(gray, rect)
    if interior is None:
        x1, y1, x2, y2 = inset(rect, 0.05)
        interior = np.zeros_like(gray)
        interior[y1:y2, x1:x2] = 1
        return interior, inset(rect, INSET)
    x, y, w, h = cv2.boundingRect(interior)
    return interior, inset((x, y, x + w, y + h), INSET)


def ink_mask(gray: NDArray[np.uint8], regions: list[Mask]) -> Mask:
    ink = (gray < INK).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    ink = cv2.dilate(ink, kernel).astype(np.uint8)
    inside = np.zeros_like(gray)
    for region in regions:
        inside |= region
    return (ink & inside) * 255


def text_width(font: ImageFont.FreeTypeFont, text: str) -> int:
    left, _, right, _ = font.getbbox(text)
    return int(right - left)


def wrap(text: str, font: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}".strip()
            if line and text_width(font, candidate) > width:
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
    for size in range(min(MAX_FONT, height), MIN_FONT, -1):
        font = ImageFont.truetype(str(FONT), size)
        lines = wrap(text, font, width)
        fits_width = all(text_width(font, line) <= width for line in lines)
        if fits_width and len(lines) * line_height(font) <= height:
            return font, lines
    font = ImageFont.truetype(str(FONT), MIN_FONT)
    return font, wrap(text, font, width)


def draw_text(draw: ImageDraw.ImageDraw, text: str, rect: Rect) -> None:
    x1, y1, x2, y2 = rect
    width, height = x2 - x1, y2 - y1
    if width <= 0 or height <= 0 or not text.strip():
        return
    font, lines = fit(text, width, height)
    step = line_height(font)
    y = y1 + (height - step * len(lines)) / 2
    for line in lines:
        x = x1 + (width - text_width(font, line)) / 2
        draw.text((x, y), line, font=font, fill="black")
        y += step


def render(image: Image.Image, bubbles: list[dict[str, Any]]) -> Image.Image:
    rgb = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.uint8)
    todo = [b for b in bubbles if b["kind"] not in SKIPPED_KINDS and b["translation"].strip()]
    regions, targets = [], []
    for bubble in todo:
        region, target = region_of(gray, tuple(bubble["bbox"]))
        regions.append(region)
        targets.append(target)
    cleaned = cv2.inpaint(rgb, ink_mask(gray, regions), INPAINT_RADIUS, cv2.INPAINT_TELEA)
    out = Image.fromarray(cleaned)
    draw = ImageDraw.Draw(out)
    for bubble, target in zip(todo, targets, strict=True):
        draw_text(draw, bubble["translation"], target)
    return out
