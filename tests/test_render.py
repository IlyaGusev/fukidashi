import numpy as np
from PIL import Image, ImageDraw, ImageFont

from panelogue.render import ink_mask, region_of, render

SOURCE_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LOOSE_BOX = (140, 150, 260, 300)


def bubble_page() -> Image.Image:
    page = Image.new("RGB", (400, 600), "gray")
    draw = ImageDraw.Draw(page)
    draw.ellipse((100, 100, 300, 400), fill="white", outline="black", width=4)
    draw.text((150, 200), "SOURCE", font=ImageFont.truetype(SOURCE_FONT, 28), fill="black")
    return page


def dark(image: Image.Image, box: tuple[int, int, int, int]) -> int:
    return int((np.array(image.convert("L").crop(box)) < 128).sum())


def test_loose_box_still_covers_the_whole_bubble() -> None:
    gray = np.array(bubble_page().convert("L"))
    region, (x1, y1, x2, y2) = region_of(gray, LOOSE_BOX)
    assert 100 < x1 < 150 and 250 < x2 < 300 and 100 < y1 < 150 and 350 < y2 < 400
    mask = ink_mask(gray, [region])
    assert mask[210, 160] == 255
    assert mask[100, 200] == 0


def test_render_replaces_text_and_keeps_outline() -> None:
    page = bubble_page()
    out = render(page, [{"bbox": list(LOOSE_BOX), "kind": "speech", "translation": "Hi"}])
    assert out.size == page.size
    assert dark(out, (150, 200, 260, 230)) < dark(page, (150, 200, 260, 230)) / 4
    assert dark(out, (110, 110, 290, 390)) > 0
    assert dark(out, (98, 240, 106, 260)) > 0


def test_sfx_and_empty_translations_are_left_alone() -> None:
    page = bubble_page()
    bubbles = [
        {"bbox": list(LOOSE_BOX), "kind": "sfx", "translation": "BOOM"},
        {"bbox": list(LOOSE_BOX), "kind": "speech", "translation": " "},
    ]
    assert np.array_equal(np.array(render(page, bubbles)), np.array(page))
