# Work plan for three people

## Decide first

Do the three people build the prose edition or the manga demo? The plan puts
prose first and gates visual work behind section 8.3. The only code in the repo
is the manga bubble detector (`scripts/detect_bubbles.py`). The split below
assumes prose first, with the detector as a side track. The swap is at the end.

## Split by the three seams in section 7.1

Each person owns one package and starts against a fixture, so nobody waits.

### Person A: source and translation pipeline (ML/backend)

- DOCX to frozen `SourceRevision` with unit IDs and preflight flags.
- Story bible (`ContextRevision`) with source links.
- Scene-aware `TranslationUnit` drafts with uncertainty flags.
- Omission and addition checks.
- Resumable job runner with retries and a spend cap.
- Side track after drafts land: turn `scripts/detect_bubbles.py` into the
  visual adapter that emits `Page` and `TextRegion` records.

### Person B: editorial workspace and export (product/frontend)

- Review view per unit: source, target, evidence, issues, alternatives,
  approval state.
- Protected edits: a regeneration proposes changes and never overwrites
  accepted text.
- Glossary change produces an impact list.
- EPUB export from accepted units, EPUBCheck, metadata, credits.
- Output is an immutable `EditionRevision`.
- Starts on a hand-made fixture of about 20 units.

### Person C: store, release gate, and money

- Title page, sample, disclosures, price and VAT.
- Stripe checkout, idempotent webhooks, `Order` and `Entitlement`.
- Delivery of the stored file, refunds.
- Release gate that blocks sale until rights, review, file checks, and offer
  approval exist.
- `RoyaltyLedger` and per-edition cost tracking.
- Starts on a hand-made EPUB and a fake `EditionRevision`.

## Shared work on day 1 (half a day, all three)

Freeze the entity schema from section 7.2 as one module: `Work`,
`SourceRevision`, `ContextRevision`, `TranslationUnit`, `Issue` and
`ReviewDecision`, `EditionRevision`, `Offer`, `Order` and `Entitlement`.
After that, each person touches only their own package plus small PRs to the
schema.

## Two handoff contracts

- A to B: a list of `TranslationUnit`s with source mapping, draft,
  alternatives, and flags.
- B to C: an `EditionRevision` with file hash, review record, rights
  reference, and release permission.

## Integration milestone at week 4

As in section 14.1: one book end to end. DOCX in, reviewed EPUB out, test
purchase delivered. Weeks 5 to 8 fix what breaks.

## Why this split works

It matches the three surfaces in 6.1 and the three columns in 14.1. Load is
close to even: A has the hardest ML, B has the most UI, C has the most
integration and configuration. Packages do not overlap, so merges stay small.

## If the target is the manga demo instead

- A: extraction from the existing script, reading order, speaker attribution,
  context-aware translation.
- B: page review UI, real font rendering inside each bbox, overflow flags,
  lettering handoff.
- C: page reader with direction, spreads, and zoom, plus delivery and
  entitlement.

## Not in this split

Rights, the editor, and reader interviews. The plan gives them to the founder.
That person loses about a third of their build time. Give them seam C. It has
the most external waits, so it pauses well.
