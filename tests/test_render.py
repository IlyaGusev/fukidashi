import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fukidashi.render import FONT, ink_mask, place, render

BUBBLE = (100, 100, 300, 400)
TEXT = (150, 200, 260, 230)
LOOSE_BOX = (140, 150, 260, 300)


def bubble_page() -> Image.Image:
    page = Image.new("RGB", (400, 600), "gray")
    draw = ImageDraw.Draw(page)
    draw.ellipse(BUBBLE, fill="white", outline="black", width=4)
    draw.text(TEXT[:2], "SOURCE", font=ImageFont.truetype(str(FONT), 28), fill="black")
    return page


def dark(image: Image.Image, box: tuple[int, int, int, int]) -> int:
    return int((np.array(image.convert("L").crop(box)) < 128).sum())


def test_loose_box_still_covers_the_whole_bubble() -> None:
    gray = np.array(bubble_page().convert("L"))
    inside = np.zeros_like(gray)
    target = place(gray, inside, LOOSE_BOX)
    assert all(abs(t - b) < 50 for t, b in zip(target, BUBBLE, strict=True))
    mask = ink_mask(gray, inside)
    assert mask[210, 160] == 1
    assert mask[100, 200] == 0


def test_render_replaces_text_and_keeps_outline() -> None:
    page = bubble_page()
    out = render(page, [{"bbox": list(LOOSE_BOX), "kind": "speech", "translation": "Hi"}])
    assert dark(out, TEXT) < dark(page, TEXT) / 4
    assert dark(out, BUBBLE) > 0
    assert dark(out, (98, 240, 106, 260)) > 0


def test_text_stays_inside_a_jagged_bubble() -> None:
    page = Image.new("RGB", (400, 400), "gray")
    draw = ImageDraw.Draw(page)
    draw.rectangle((150, 50, 250, 350), fill="white", outline="black", width=4)
    draw.rectangle((50, 150, 350, 250), fill="white", outline="black", width=4)
    draw.rectangle((154, 150, 246, 250), fill="white")
    gray = np.array(page.convert("L"))
    inside = np.zeros_like(gray)
    x1, y1, x2, y2 = place(gray, inside, (120, 120, 280, 280))
    assert inside[y1:y2, x1:x2].all()
    assert (x2 - x1) * (y2 - y1) >= 80 * 280


def test_sfx_and_empty_translations_are_left_alone() -> None:
    page = bubble_page()
    bubbles = [
        {"bbox": list(LOOSE_BOX), "kind": "sfx", "translation": "BOOM"},
        {"bbox": list(LOOSE_BOX), "kind": "speech", "translation": " "},
    ]
    assert np.array_equal(np.array(render(page, bubbles)), np.array(page))
