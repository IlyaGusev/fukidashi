import json
from pathlib import Path

import fire
from sacrebleu.metrics.chrf import CHRF

from fukidashi.compare import Bubble, Rendering, final_glossary, mentions, page_bubbles, renders

MIN_USES = 3
MAX_TERMS = 20
CELL_CHARS = 70
OUT = Path("out/audit")
NAMES_TITLE = "## Glossary terms used {uses}+ times and not always rendered as the glossary says"
NAMES_HEADER = "| source | target | uses | matches | a translation without it | its reference |"


def cell(text: str) -> str:
    flat = " ".join(text.split()).replace("|", "/")
    return flat if len(flat) <= CELL_CHARS else flat[: CELL_CHARS - 1] + "…"


def name_rows(bubbles: list[Bubble], glossary: list[Rendering]) -> list[str]:
    rows = []
    for pair in glossary:
        uses = [b for b in bubbles if mentions(b, pair.source)]
        misses = [b for b in uses if not renders(b.translation, pair.target)]
        if len(uses) >= MIN_USES and misses:
            rows.append(
                f"| {pair.source} | {cell(pair.target)} | {len(uses)} | "
                f"{len(uses) - len(misses)} | {cell(misses[0].translation)} | "
                f"{cell(misses[0].reference)} |"
            )
    return rows[:MAX_TERMS]


def worst_rows(pages: list[list[Bubble]], count: int) -> list[str]:
    chrf = CHRF()
    scored = [
        (chrf.sentence_score(b.translation.lower(), [b.reference.lower()]).score, number, b)
        for number, bubbles in enumerate(pages, start=1)
        for b in bubbles
        if b.reference.strip()
    ]
    scored.sort(key=lambda row: row[0])
    return [
        f"| {number} | {cell(b.source)} | {cell(b.reference)} | {cell(b.translation)} | "
        f"{score:.1f} |"
        for score, number, b in scored[:count]
    ]


def main(path: str, worst: int = 15) -> None:
    volume = json.loads(Path(path).read_text(encoding="utf-8"))
    pages = list(page_bubbles(volume).values())
    bubbles = [b for page in pages for b in page]
    report = "\n".join(
        [
            f"# {Path(path).stem}",
            "",
            NAMES_TITLE.format(uses=MIN_USES),
            "",
            NAMES_HEADER,
            "|---|---|---|---|---|---|",
            *name_rows(bubbles, final_glossary(volume)),
            "",
            f"## {worst} lines with the lowest chrF",
            "",
            "| page | Japanese | reference | ours | chrF |",
            "|---|---|---|---|---|",
            *worst_rows(pages, worst),
        ]
    )
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{Path(path).stem}.md"
    out.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    fire.Fire(main)
