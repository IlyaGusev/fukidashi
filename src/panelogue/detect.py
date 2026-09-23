import base64
import functools
import json
import mimetypes
import os
import urllib.request
from collections.abc import Callable
from io import BytesIO
from typing import Any

import openai
from openai import AsyncOpenAI
from PIL import Image, ImageDraw

BASE_URL = "https://api.tokenfactory.nebius.com/v1"
MODEL = "zai-org/GLM-5.3-Flash"
LANG = "English"

PROMPT = """\
This is a page from a manga or comic ({w}x{h} pixels).
Find every text container: speech bubbles, thought bubbles, narration boxes and sound effects.
For each one return its bounding box in pixel coordinates, the text inside it transcribed exactly in the original language, and a natural translation into {lang}.
Reading order: right-to-left, top-to-bottom for manga; left-to-right for western comics.
{context}
Answer with JSON only, no prose, in this shape:
{{"bubbles": [{{"bbox": [x1, y1, x2, y2], "kind": "speech|thought|narration|sfx", "text": "...", "translation": "..."}}]}}
"""  # noqa: E501

CONTEXT = """
Text from the previous page, for consistent names, terms and tone:
{lines}
"""

Progress = Callable[[str, int], None]


class BadOutput(ValueError):
    pass


def no_progress(phase: str, chars: int) -> None:
    pass


@functools.cache
def client() -> AsyncOpenAI:
    stall = float(os.environ.get("PANELOGUE_STALL_TIMEOUT", "60"))
    return AsyncOpenAI(
        base_url=BASE_URL,
        api_key=os.environ["NEBIUS_API_TOKEN"],
        timeout=openai.Timeout(connect=10, read=stall, write=30, pool=10),
        max_retries=0,
    )


async def list_vision_models() -> list[str]:
    models = (await client().models.list(extra_query={"verbose": "true"})).data
    return sorted(
        m.id for m in models if "image" in (m.model_extra or {})["architecture"]["modality"]
    )


def read_source(src: str) -> tuple[bytes, str]:
    if src.startswith(("http://", "https://")):
        with urllib.request.urlopen(src) as r:
            return r.read(), r.headers.get_content_type()
    with open(src, "rb") as f:
        return f.read(), mimetypes.guess_type(src)[0] or "image/png"


def strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return text


def clamp(value: int, limit: int) -> int:
    return max(0, min(limit, value))


def clean_bubble(raw: Any, w: int, h: int) -> dict[str, Any]:
    try:
        x1, y1, x2, y2 = (int(v) for v in raw["bbox"])
        return {
            "bbox": [clamp(x1, w), clamp(y1, h), clamp(x2, w), clamp(y2, h)],
            "kind": str(raw.get("kind") or "speech"),
            "text": str(raw.get("text") or ""),
            "translation": str(raw.get("translation") or ""),
        }
    except (KeyError, TypeError, ValueError) as e:
        raise BadOutput(f"malformed bubble: {str(raw)[:120]}") from e


def parse_bubbles(text: str, w: int, h: int) -> list[dict[str, Any]]:
    try:
        data = json.loads(strip_fence(text))
    except json.JSONDecodeError as e:
        raise BadOutput(f"invalid JSON after {len(text)} chars: {e}") from e
    bubbles = data.get("bubbles") if isinstance(data, dict) else None
    if not isinstance(bubbles, list):
        raise BadOutput("answer has no bubbles list")
    return [clean_bubble(b, w, h) for b in bubbles]


async def stream_completion(
    kwargs: dict[str, Any], on_progress: Progress
) -> tuple[str, dict[str, Any]]:
    stream = await client().chat.completions.create(
        **kwargs, stream=True, stream_options={"include_usage": True}
    )
    parts: list[str] = []
    usage: dict[str, Any] = {}
    seen = 0
    async for chunk in stream:
        if chunk.usage:
            usage = chunk.usage.model_dump(exclude_none=True)
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            parts.append(delta.content)
        piece = delta.content or getattr(delta, "reasoning_content", None)
        if piece:
            seen += len(piece)
            on_progress("writing" if delta.content else "thinking", seen)
    return "".join(parts), usage


async def detect_bytes(
    data: bytes,
    mime: str,
    model: str = MODEL,
    thinking: bool = False,
    lang: str = LANG,
    context: list[str] | None = None,
    on_progress: Progress = no_progress,
) -> tuple[Image.Image, dict[str, Any]]:
    img = Image.open(BytesIO(data))
    w, h = img.size
    url = f"data:{mime};base64,{base64.b64encode(data).decode()}"
    ctx = CONTEXT.format(lines="\n".join(f"- {t}" for t in context)) if context else ""
    content = [
        {"type": "image_url", "image_url": {"url": url}},
        {"type": "text", "text": PROMPT.format(w=w, h=h, lang=lang, context=ctx)},
    ]
    kwargs: dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "max_tokens": 8192,
        "extra_body": {"chat_template_kwargs": {"thinking": thinking, "enable_thinking": thinking}},
        "messages": [{"role": "user", "content": content}],
    }
    try:
        text, usage = await stream_completion(
            {**kwargs, "response_format": {"type": "json_object"}}, on_progress
        )
    except openai.BadRequestError:
        text, usage = await stream_completion(kwargs, on_progress)
    return img, {
        "bubbles": parse_bubbles(text, w, h),
        "size": [w, h],
        "model": model,
        "thinking": thinking,
        "lang": lang,
        "usage": usage,
    }


async def detect(
    src: str, model: str = MODEL, thinking: bool = False, lang: str = LANG
) -> tuple[Image.Image, dict[str, Any]]:
    data, mime = read_source(src)
    return await detect_bytes(data, mime, model, thinking, lang)


def draw(img: Image.Image, result: dict[str, Any], out: str) -> None:
    img = img.convert("RGB")
    d = ImageDraw.Draw(img)
    for i, b in enumerate(result["bubbles"]):
        x1, y1, x2, y2 = b["bbox"]
        d.rectangle([x1, y1, x2, y2], outline="red", width=3)
        d.text((x1 + 4, y1 + 4), str(i), fill="red")
    img.save(out)
