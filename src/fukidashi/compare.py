import re
import unicodedata
from typing import Any, NamedTuple

MIN_SOURCE_CHARS = 2


class Bubble(NamedTuple):
    source: str
    reference: str
    translation: str


class Rendering(NamedTuple):
    source: str
    target: str


def fold_source(text: str) -> str:
    return "".join(unicodedata.normalize("NFKC", text).split())


def fold_target(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    plain = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^\w\s]", " ", plain).split())


def renders(text: str, target: str) -> bool:
    folded = fold_target(target)
    word = r"(?<!\w)" + re.escape(folded) + r"(?:e?s)?(?!\w)"
    return bool(folded) and re.search(word, fold_target(text)) is not None


def mentions(bubble: Bubble, source: str) -> bool:
    return source in fold_source(bubble.source)


def page_bubbles(volume: dict[str, Any]) -> dict[str, list[Bubble]]:
    return {
        page["imageUrl"]: [
            Bubble(
                str(b.get("text") or ""),
                str(b.get("reference") or ""),
                str(b.get("translation") or ""),
            )
            for b in page["bubbles"]
        ]
        for page in volume["pages"]
    }


def shared_images(volumes: list[dict[str, Any]]) -> list[str]:
    first, *rest = volumes
    others = [set(page_bubbles(v)) for v in rest]
    return [p["imageUrl"] for p in first["pages"] if all(p["imageUrl"] in o for o in others)]


def shared_bubbles(volume: dict[str, Any], images: list[str]) -> list[Bubble]:
    pages = page_bubbles(volume)
    return [b for image in images for b in pages[image]]


def final_glossary(volume: dict[str, Any]) -> list[Rendering]:
    snapshots = volume.get("snapshots") or []
    glossary = snapshots[-1].get("glossary", []) if snapshots else []
    pairs = [Rendering(fold_source(str(t["source"])), str(t.get("target") or "")) for t in glossary]
    return [p for p in pairs if len(p.source) >= MIN_SOURCE_CHARS and fold_target(p.target)]


def candidate_renderings(volumes: list[dict[str, Any]]) -> dict[str, set[str]]:
    candidates: dict[str, set[str]] = {}
    for volume in volumes:
        for pair in final_glossary(volume):
            candidates.setdefault(pair.source, set()).add(pair.target)
    return candidates


def glossary_adherence(bubbles: list[Bubble], glossary: list[Rendering]) -> float | None:
    uses = [(b, pair) for b in bubbles for pair in glossary if mentions(b, pair.source)]
    if not uses:
        return None
    return sum(renders(b.translation, pair.target) for b, pair in uses) / len(uses)


def professional_checks(
    bubbles: list[Bubble], candidates: dict[str, set[str]]
) -> list[tuple[Bubble, list[str]]]:
    checks = []
    for b in bubbles:
        for source, targets in candidates.items():
            used_by_reference = [t for t in targets if renders(b.reference, t)]
            if mentions(b, source) and used_by_reference:
                checks.append((b, used_by_reference))
    return checks


def reference_agreement(bubbles: list[Bubble], candidates: dict[str, set[str]]) -> float | None:
    checks = professional_checks(bubbles, candidates)
    if not checks:
        return None
    agreed = sum(any(renders(b.translation, t) for t in targets) for b, targets in checks)
    return agreed / len(checks)


def page_stats(volume: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        page["imageUrl"]: stats
        for page, stats in zip(volume["pages"], volume.get("memoryStats") or [], strict=False)
    }


def score_run(
    volume: dict[str, Any], images: list[str], candidates: dict[str, set[str]], first: int
) -> dict[str, Any]:
    stats = page_stats(volume)
    bubbles = shared_bubbles(volume, images)
    early = shared_bubbles(volume, images[:first])
    return {
        "pages": len(images),
        "startConfidence": stats[images[0]]["confidence"] if images[0] in stats else None,
        "memoryFailed": sum(bool(stats[i]["memoryFailed"]) for i in images if i in stats),
        "glossaryAdherence": glossary_adherence(bubbles, final_glossary(volume)),
        "referenceAgreement": reference_agreement(bubbles, candidates),
        "earlyReferenceAgreement": reference_agreement(early, candidates),
    }
