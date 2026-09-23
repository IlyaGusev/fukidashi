import base64
import json
import mimetypes
import os
import urllib.request
from io import BytesIO

import openai
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


def client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=os.environ["NEBIUS_API_TOKEN"])


def list_vision_models() -> list[str]:
    models = client().models.list(extra_query={"verbose": "true"}).data
    return sorted(m.id for m in models if "image" in m.model_extra["architecture"]["modality"])


def read_source(src: str) -> tuple[bytes, str]:
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src) as r:
            return r.read(), r.headers.get_content_type()
    with open(src, "rb") as f:
        return f.read(), mimetypes.guess_type(src)[0] or "image/png"


def parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def detect_bytes(data: bytes, mime: str, model: str = MODEL, thinking: bool = False) -> tuple[Image.Image, dict]:
    img = Image.open(BytesIO(data))
    w, h = img.size
    url = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    kwargs = dict(
        model=model,
        temperature=0,
        max_tokens=65536,
        extra_body={"chat_template_kwargs": {"enable_thinking": thinking}},
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": url}},
                {"type": "text", "text": PROMPT.format(w=w, h=h)},
            ],
        }],
    )
    try:
        resp = client().chat.completions.create(**kwargs, response_format={"type": "json_object"})
    except openai.BadRequestError:
        resp = client().chat.completions.create(**kwargs)
    result = parse_json(resp.choices[0].message.content)
    for b in result["bubbles"]:
        x1, y1, x2, y2 = b["bbox"]
        b["bbox"] = [max(0, min(w, x1)), max(0, min(h, y1)), max(0, min(w, x2)), max(0, min(h, y2))]
    result["size"] = [w, h]
    result["model"] = model
    result["thinking"] = thinking
    result["usage"] = resp.usage.model_dump(exclude_none=True)
    return img, result


def detect(src: str, model: str = MODEL, thinking: bool = False) -> tuple[Image.Image, dict]:
    data, mime = read_source(src)
    return detect_bytes(data, mime, model, thinking)


def draw(img: Image.Image, result: dict, out: str) -> None:
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    for i, b in enumerate(result["bubbles"]):
        x1, y1, x2, y2 = b["bbox"]
        d.rectangle([x1, y1, x2, y2], outline="red", width=3)
        d.text((x1 + 4, y1 + 4), str(i), fill="red")
    img.save(out)
