"""Detect speech bubbles and their text on a manga/comic page with a VLM.

Usage:
    uv run detect_bubbles.py page.png [--draw out.png]
    uv run detect_bubbles.py https://example.com/page.jpg
"""

import argparse
import base64
import io
import json
import mimetypes
import os
import sys
import urllib.request

from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageDraw

BASE_URL = "https://api.tokenfactory.nebius.com/v1"
MODEL = "zai-org/GLM-5.3-Flash"

PROMPT = """\
This is a page from a manga or comic ({w}x{h} pixels).
Find every text container: speech bubbles, thought bubbles, narration boxes and sound effects.
For each one return its bounding box in pixel coordinates and the text inside it, transcribed exactly in the original language.
Reading order: right-to-left, top-to-bottom for manga; left-to-right for western comics.

Answer with JSON only, no prose, in this shape:
{{"bubbles": [{{"bbox": [x1, y1, x2, y2], "kind": "speech|thought|narration|sfx", "text": "..."}}]}}
"""


def load_image(src: str) -> tuple[Image.Image, str]:
    """Return the image and a URL the API can fetch (http(s) or data URI)."""
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src) as r:
            data = r.read()
        return Image.open(io.BytesIO(data)), src
    with open(src, "rb") as f:
        data = f.read()
    mime = mimetypes.guess_type(src)[0] or "image/png"
    b64 = base64.b64encode(data).decode()
    return Image.open(io.BytesIO(data)), f"data:{mime};base64,{b64}"


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def detect(src: str) -> dict:
    img, url = load_image(src)
    w, h = img.size
    client = OpenAI(base_url=BASE_URL, api_key=os.environ["NEBIUS_API_TOKEN"])
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": url}},
                {"type": "text", "text": PROMPT.format(w=w, h=h)},
            ],
        }],
    )
    result = parse_json(resp.choices[0].message.content)
    for b in result["bubbles"]:
        x1, y1, x2, y2 = b["bbox"]
        b["bbox"] = [max(0, min(w, x1)), max(0, min(h, y1)), max(0, min(w, x2)), max(0, min(h, y2))]
    result["size"] = [w, h]
    return img, result


def draw(img: Image.Image, result: dict, out: str) -> None:
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    for i, b in enumerate(result["bubbles"]):
        x1, y1, x2, y2 = b["bbox"]
        d.rectangle([x1, y1, x2, y2], outline="red", width=3)
        d.text((x1 + 4, y1 + 4), str(i), fill="red")
    img.save(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="local path or http(s) URL")
    ap.add_argument("--draw", metavar="OUT.png", help="save a copy with boxes drawn")
    args = ap.parse_args()

    load_dotenv()
    img, result = detect(args.image)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()
    if args.draw:
        draw(img, result, args.draw)


if __name__ == "__main__":
    main()
