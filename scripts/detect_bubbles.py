import asyncio
import json

import fire

from fukidashi.detect import detect, draw
from fukidashi.settings import settings


def main(
    image: str,
    draw_to: str | None = None,
    model: str = settings.model,
    thinking: bool = False,
    lang: str = settings.lang,
) -> None:
    img, result = asyncio.run(detect(image, model=model, thinking=thinking, lang=lang))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if draw_to:
        draw(img, result, draw_to)


if __name__ == "__main__":
    fire.Fire(main)
