import json

import fire
from dotenv import load_dotenv

from panelogue.detect import MODEL, detect, draw


def main(image: str, draw_to: str | None = None, model: str = MODEL, thinking: bool = False) -> None:
    load_dotenv()
    img, result = detect(image, model=model, thinking=thinking)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if draw_to:
        draw(img, result, draw_to)


if __name__ == "__main__":
    fire.Fire(main)
