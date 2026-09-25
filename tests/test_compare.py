from typing import Any

from fukidashi.compare import (
    Bubble,
    Rendering,
    candidate_renderings,
    final_glossary,
    glossary_adherence,
    reference_agreement,
    renders,
    score_run,
    shared_images,
)

PAGES = {
    "p1.jpg": [("在藤", "arifuji")],
    "p2.jpg": [("いいぞ在藤", "good, arifuji")],
    "p3.jpg": [("宏也", "hiroya"), ("見ろ", "look.")],
    "p4.jpg": [("在藤、宏也を見ろ", "arifuji, look at hiroya")],
}


def volume(
    translations: dict[str, list[str]],
    glossary: list[tuple[str, str]],
    confidences: list[int],
) -> dict[str, Any]:
    pages = [
        {
            "imageUrl": image,
            "bubbles": [
                {"text": ja, "reference": en, "translation": text}
                for (ja, en), text in zip(PAGES[image], translations[image], strict=True)
            ],
        }
        for image in translations
    ]
    stats = [{"confidence": c, "memoryFailed": False} for c in confidences]
    terms = [{"source": s, "target": t, "note": ""} for s, t in glossary]
    return {"pages": pages, "memoryStats": stats, "snapshots": [{"glossary": terms}]}


def cold() -> dict[str, Any]:
    return volume(
        {
            "p3.jpg": ["Kouya", "Look"],
            "p4.jpg": ["Zaitou, look at Hiroya!"],
        },
        [("宏也", "Hiroya"), ("在藤", "Zaitou")],
        [40, 70],
    )


def seeded() -> dict[str, Any]:
    return volume(
        {
            "p3.jpg": ["Hiroya", "Look"],
            "p4.jpg": ["Arifuji, look at Hiroya!"],
        },
        [("宏也", "Hiroya"), ("在藤", "Arifuji")],
        [90, 95],
    )


def full() -> dict[str, Any]:
    return volume(
        {
            "p1.jpg": ["Arifuji"],
            "p2.jpg": ["Good, Arifuji"],
            "p3.jpg": ["Hiroya", "Look"],
            "p4.jpg": ["Arifuji, look at Hiroya!"],
        },
        [("在藤", "Arifuji"), ("宏也", "Hiroya")],
        [50, 70, 85, 95],
    )


def test_renders_ignores_case_accents_and_suffixes() -> None:
    assert renders("Arifuji's sword", "arifuji")
    assert renders("the OKAMI returns", "Ōkami")
    assert not renders("Marifuji", "Arifuji")
    assert not renders("anything", "!!")


def test_shared_images_keeps_only_pages_in_every_run() -> None:
    assert shared_images([full(), cold(), seeded()]) == ["p3.jpg", "p4.jpg"]


def test_final_glossary_skips_one_character_sources_and_empty_targets() -> None:
    v = volume({"p1.jpg": ["Arifuji"]}, [("在藤", "Arifuji"), ("ッ", "Tch"), ("見ろ", "")], [50])
    assert final_glossary(v) == [Rendering("在藤", "Arifuji")]


def test_glossary_adherence_catches_a_name_that_drifted() -> None:
    bubbles = [Bubble("宏也", "hiroya", "Kouya"), Bubble("宏也を見ろ", "look at hiroya", "Hiroya!")]
    assert glossary_adherence(bubbles, [Rendering("宏也", "Hiroya")]) == 0.5
    assert glossary_adherence(bubbles, []) is None


def test_reference_agreement_uses_renderings_the_professionals_used() -> None:
    runs = [cold(), seeded()]
    candidates = candidate_renderings(runs)
    assert candidates == {"宏也": {"Hiroya"}, "在藤": {"Zaitou", "Arifuji"}}
    cold_bubbles = [Bubble("在藤", "arifuji", "Zaitou"), Bubble("宏也", "hiroya", "Hiroya")]
    seeded_bubbles = [Bubble("在藤", "arifuji", "Arifuji"), Bubble("宏也", "hiroya", "Hiroya")]
    assert reference_agreement(cold_bubbles, candidates) == 0.5
    assert reference_agreement(seeded_bubbles, candidates) == 1.0
    assert reference_agreement([Bubble("見ろ", "look.", "Look")], candidates) is None


def test_score_run_compares_runs_on_the_same_pages() -> None:
    runs = [cold(), seeded(), full()]
    images = shared_images(runs)
    candidates = candidate_renderings(runs)
    cold_score, seeded_score, full_score = (score_run(v, images, candidates, 1) for v in runs)
    assert cold_score == {
        "pages": 2,
        "startConfidence": 40,
        "memoryFailed": 0,
        "glossaryAdherence": 2 / 3,
        "referenceAgreement": 1 / 3,
        "earlyReferenceAgreement": 0.0,
    }
    assert seeded_score["startConfidence"] == 90
    assert seeded_score["glossaryAdherence"] == 1.0
    assert seeded_score["referenceAgreement"] == 1.0
    assert full_score["startConfidence"] == 85
    assert full_score["referenceAgreement"] == 1.0
