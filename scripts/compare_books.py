import json
from pathlib import Path
from typing import Any

import fire
from sacrebleu.metrics.chrf import CHRF

from fukidashi.compare import Bubble, candidate_renderings, score_run, shared_bubbles, shared_images


def chrf(bubbles: list[Bubble]) -> float:
    if not bubbles:
        return 0.0
    hypotheses = [b.translation.lower() for b in bubbles]
    references = [b.reference.lower() for b in bubbles]
    return float(CHRF().corpus_score(hypotheses, [references]).score)


def cell(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def print_table(rows: list[dict[str, Any]]) -> None:
    columns = list(rows[0])
    print("| " + " | ".join(columns) + " |")
    print("|" + "---|" * len(columns))
    for row in rows:
        print("| " + " | ".join(cell(row[c]) for c in columns) + " |")


def main(*paths: str, first: int = 5) -> None:
    volumes = [json.loads(Path(p).read_text(encoding="utf-8")) for p in paths]
    images = shared_images(volumes)
    if not images:
        raise SystemExit("the volumes have no pages in common")
    candidates = candidate_renderings(volumes)
    rows = []
    for path, volume in zip(paths, volumes, strict=True):
        rows.append(
            {
                "run": Path(path).stem,
                **score_run(volume, images, candidates, first),
                "chrf": chrf(shared_bubbles(volume, images)),
                f"chrfFirst{first}": chrf(shared_bubbles(volume, images[:first])),
            }
        )
    print(f"{len(images)} shared pages, early metrics on the first {first}")
    print_table(rows)


if __name__ == "__main__":
    fire.Fire(main)
