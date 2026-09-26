import json
from pathlib import Path

import fire
from sacrebleu.metrics.chrf import CHRF

from fukidashi.compare import Bubble, page_bubbles


def volume_bubbles(path: str) -> list[Bubble]:
    volume = json.loads(Path(path).read_text(encoding="utf-8"))
    return [b for bubbles in page_bubbles(volume).values() for b in bubbles]


def main(*paths: str) -> None:
    bubbles = [b for path in paths for b in volume_bubbles(path)]
    hypotheses = [b.translation for b in bubbles]
    references = [b.reference for b in bubbles]
    score = CHRF().corpus_score(hypotheses, [references]).score
    print(f"{len(paths)} volumes, {len(bubbles)} bubbles, chrF {score:.1f} (paper protocol)")


if __name__ == "__main__":
    fire.Fire(main)
