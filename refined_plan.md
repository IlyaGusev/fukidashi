# More manga. In English.
*A direct-to-reader publisher of licensed Japanese manga in English*

**Discover the manga you have been missing. Read complete, authorized volumes. Keep the voice of the original.**

> Your next favorite manga may already exist, just not in English. We find compelling Japanese manga, license it from its rights holders, and bring carefully reviewed English volumes to readers. Readers discover and buy the volumes. Creators share in the sales. A whole-volume localization workflow makes each new edition a more repeatable production.

**Business in one sentence:** A specialist digital publisher that licenses Japanese manga with unmet English-language demand, produces complete, human-reviewed English volumes with an AI-assisted whole-volume workflow, and sells them directly to readers.

**Plan date:** 23 September 2026.
**Research basis:** Sources and research notes dated 22 September 2026, plus general market knowledge flagged as unresearched where used.
**Working establishment:** Netherlands-based publisher and consumer seller.
**Market hypothesis:** English-language manga readers, marketed first to readers in the United States and United Kingdom, with EU English readers served from the same store.
**Launch scope:** One language pair (Japanese to English), one format (page-based black-and-white manga volume), one released volume before broadening the catalog.
**Commercial status:** Proposed business, product, terms, budgets, and targets. Not an operating service, acquired catalog, or validated forecast.

**Scope of this version.** Earlier drafts covered prose novels, English-language comics, a German launch, and a professional production-software offer. This version drops all of them. Prose, other source languages, other target languages, reader uploads, and software sales are out of scope until the manga catalog earns its own contribution.

### The business at a glance

| Decision | Proposed direction |
|---|---|
| Primary customer | An English-language reader who already buys digital manga and can name a series or creator with no English edition |
| Supply partners | Rights-controlling manga creators, small and independent Japanese publishers, and their agents |
| Core product | A complete, stable, authorized English volume, not an on-demand translation |
| Production foundation | Immutable source pages, whole-volume context, source-linked translation, protected editorial corrections, letterer-tested handoff, human review, controlled release |
| Catalog identity | A coherent readership and editorial promise across a small number of related series |
| Revenue | Individual volume purchases and subsequent purchases from the catalog |
| First catalog | Rights discussions for up to three related volumes from at least two rights holders; production funding for two |
| First delivery | A tested browser page reader, plus downloadable files where the license permits |
| Initial spending | €25,000 discretionary validation envelope plus three months of a proposed €8,000 monthly operating budget: €49,000 |
| Expansion rule | Add the next volume, series, or market only when rights, editorial capacity, reader demand, and contribution support it |

All prices, labor estimates, royalties, acquisition assumptions, and timelines are planning choices. External references describe populations, products, rules, and dates in the source register; they do not establish this company's traction. Legal material identifies the authorization route and the questions for qualified advisers, not clearance of a particular title or checkout.

## Contents

1. [Strategy](#strategy)
2. [Readers, rights partners, and market](#market)
3. [Catalog and rights](#catalog)
4. [Reader experience and offers](#reader-experience)
5. [Competition](#competition)
6. [Production workflow](#product)
7. [Architecture and data](#architecture)
8. [MVP and release gates](#mvp)
9. [Quality evaluation](#quality)
10. [Unit economics](#economics)
11. [Budget and cash](#finance)
12. [Rights, legal, privacy, and trust](#legal)
13. [Go-to-market](#go-to-market)
14. [Roadmap and decision gates](#roadmap)
15. [Team and operations](#operations)
16. [Risks and open decisions](#risks)
17. [Sales and partnership materials](#sales-materials)
18. [Immediate priorities](#conclusion)

**Appendices:** [A. Financial formulas](#financial-appendix) · [B. Source register](#sources)

---

<a id="strategy"></a>
## 1. Strategy

### 1.1 Sell the volume, not the translation task

The customer-facing product is a manga volume worth reading. A reader should not upload source pages, approve glossaries, or pay for a private translation. They discover a title, read a substantial sample, understand the edition they are buying, and receive a finished volume.

The promise:

> **More manga worth reading, available in English, with permission, care, and the character of the original intact.**

That means the joke still lands when its payoff arrives, the right character speaks, the reading order is correct, honorifics and forms of address follow a consistent policy, and the words sit inside the page rather than in a spreadsheet.

One accepted volume serves many readers during its licensed term. The company invests in the work once, maintains the published version, and earns later sales without regenerating the translation. The production unit is **volume × approved English edition**.

### 1.2 Why Japanese-to-English manga, and what it costs

Reasons to choose this lane:

- Licensed direct-to-reader manga sales already work as a mechanism. J-Novel Club sells individual volumes, previews, and memberships; most manga are listed at 899 coins, with 100 coins equal to US$1. [R04] [R48]
- Authorized, sales-funded creator translation programs exist. viviON Translators Unite selects, reviews, and rewards translators from sales. [R49]
- Page-based manga is where whole-volume context, speaker attribution, and page fit matter most, so the production workflow has a visible advantage to prove. [R42] [R43]

What the lane requires and does not get for free:

- A paid Japanese-to-English translator or editor, an English letterer, and an independent bilingual assessor.
- Japanese rights relationships, Japanese-language outreach, and Japanese title advice.
- Vertical text, furigana, handwriting, and sound-effect extraction that works on real pages.
- Evidence of English-language demand for specific unlicensed titles. The research basis has no measurement of the English digital manga market. That is the first research gap to close.

### 1.3 The repeatable cycle

```text
Named reader demand for a specific title
    → Available rights and a permitted sample
    → Scoped publishing agreement and production investment
    → Whole-volume localization and human editorial approval
    → One stable, complete English volume
    → Direct reader purchases and reliable delivery
    → The next volume of the series or a related title
    → Better-informed licensing and production decisions
```

The advantage is cumulative: a useful catalog, trusted editions, approved series knowledge, rights-holder relationships, and readers who return. None of it comes from access to a cheap model.

### 1.4 What the company does not do

No prose. No reader uploads or scanlation. No other source or target language. No software sold to publishers. No open marketplace. Each of these is a separate business with its own rights, team, and economics.

---

<a id="market"></a>
## 2. Readers, rights partners, and market

### 2.1 The first reader

Recruit people who already buy digital manga in English and can name a real gap. Someone who names a missing series, creator, or subgenre is a better prospect than someone who is enthusiastic about AI.

| Reader situation | Job to be done | Offer to test |
|---|---|---|
| A wanted series has no English edition | Read that series | Complete licensed volume with a substantial sample |
| An English first volume created interest, then the series stopped | Continue without an unexplained gap | A credible next-volume plan with rights secured separately |
| A genre reader wants more of a familiar experience | Discover another series that fits | A tightly curated catalog of related titles |
| A reader dislikes awkward or incomplete localization | Read without fighting the page | Clear dialogue, correct order, careful lettering, complete volumes |
| A reader already bought and enjoyed a volume | Find the next purchase | A genuinely available related volume and optional release notices |

### 2.2 Rights partners

Established English manga publishers and official simulpub apps already license the major Japanese series. This is general market knowledge, not part of the research record, and it shapes supply: the realistic first titles are creator-owned works, small-publisher series, and backlist without an English edition.

A strong first rights partner controls the work and its English digital rights, has a clear rights chain, usable source assets, and will authorize the actual AI-assisted workflow. A large Japanese following is not an English acquisition channel. Qualify English reach through communities, previous requests, or permissioned introductions.

Translators, editors, and letterers are paid production partners. Recruit willing, qualified professionals around a concrete scope, actual rates, credits, and responsibilities. Membership of an association does not mean endorsement of AI-assisted work.

### 2.3 Market evidence and its limits

| Evidence | Relevance and limitation |
|---|---|
| J-Novel Club documents translated manga, previews, individual digital purchases, memberships, and series engagement; manga at 899 coins ≈ US$8.99. [R04] [R48] | A recognizable direct-sale mechanism and a price reference. No proof of this startup's demand or margins. |
| emaqi describes a licensed manga subscription in the US and Canada. [R50] [R69] | Distribution and localization may be integrated competition. |
| viviON Translators Unite runs sales-linked authorized translation and rejects machine translation. [R49] | Creators accept revenue-share translation. Not an AI-compatible inventory source. |
| GlobalComix / INKR describe opt-in localization with rights-holder control and human translators and letterers. [R46] | Human involvement and creator control are table stakes. |
| WEBTOON CANVAS announced optional translation with a staged 2026 rollout. [R47] | Platform-native creators have alternatives. |

No source in the research basis measures the English digital manga market, its buyers, or its average price. Do not present a market size until one is sourced.

### 2.4 Choose titles where four conditions overlap

A candidate needs a plausible answer to four questions: can the rights be obtained, can the promised volume be produced, can English readers be reached, and can contribution recover the investment within the license term?

Use a scorecard, but keep editorial judgment visible. An acclaimed series with expensive rights and no reachable readership is a worse first investment than a smaller title with strong audience fit and a cooperative rights holder.

Check current English availability through official publisher and retailer information before presenting a gap as real. No named title in this plan is represented as untranslated, unlicensed, or available.

### 2.5 Validation cohort

Proposed first program: 30 English-reader interviews, 10 to 15 rights-holder conversations conducted in Japanese where needed, and paid sample assessment by two Japanese-English reviewers and one letterer.

Ask readers about the last manga they wanted and could not buy in English, what they did instead, recent purchases, discovery routes, devices, and why they abandoned a checkout. Test a real, permitted sample rather than a hypothetical willingness to pay for AI translation.

Learning gates for the first volume: 10 genuine purchases to test operations, then 50 to 100 gross orders to read an initial commercial response. Recovering a €1,500 volume needs 790 gross orders in the base case after the acquisition allowance and before overhead. At 3% and 5% purchase conversion that is roughly 26,300 and 15,800 qualified visits. These are arithmetic, not benchmarks.

### 2.6 Bottom-up sizing

Model released volumes, orders per volume, ex-tax prices, royalties, transactions, support, marketing, and production. Bound releases by signed rights, editorial capacity, and capital. Bound backlist sales by the remaining license term. A list of all manga the engine could process is neither a catalog nor a market.

---

<a id="catalog"></a>
## 3. Catalog and rights

### 3.1 An editorial identity, not an inventory dump

The launch catalog should make sense to one reader. A practical configuration is the first two volumes of one series and a compatible one-shot from a second rights holder.

Prefer complete one-shots or series with a clear continuation plan. Do not advertise a whole series when only volume one is contracted. Secure realistic sequel access before making continuity the main promise.

### 3.2 Title-acquisition record

| Field | Required information |
|---|---|
| Work | Title, creator, source edition, genre, series position, complete/ongoing status |
| Rights | Controlling party, chain of authority, existing English grants, options, territory, formats, channels, term |
| Audience | Specific English demand, permitted audience access, previous requests, comparable reader response |
| Assets | Page files, clean artwork where available, scripts, cover, metadata, fonts, promotional material |
| Production | Page count, density, reviewer availability, lettering and redraw needs, sample findings, quoted budget |
| Commercial | Proposed price, royalty basis, advance or guarantee, acquisition route, expected recovery window |
| Continuation | Sequel availability, option boundaries, approval process, next useful volume |
| Status | Lead, contact made, evaluation permitted, negotiation, signed, production-approved, released, expired |

A public creator profile, store page, or doujin listing is a discovery route, not evidence that English digital rights are available. Creator-owned material still needs review of existing grants, collaborators, and third-party content.

### 3.3 The partner proposition

> **Your manga already exists. Let's give it another audience.**
>
> We license an agreed English digital edition, organize translation, lettering, and editorial review, and sell it to readers. You keep ownership of the original and all rights outside the grant. We agree the workflow, approvals, territories, channels, reporting, and revenue share before production. The first commitment is one volume and an approved sample, not your whole catalog.

The company funds the pilot. Co-funding is possible but changes the investment and royalty arrangement and must be modeled separately.

### 3.4 Publishing terms to negotiate

A commercial brief for counsel, not contract language or market-standard terms.

| Term | Proposed approach |
|---|---|
| Work and source | Exact work and source revision; excluded third-party material |
| Grant | Translation, production copies, publication, making available, sale, delivery, agreed promotional use |
| Language and territory | English; territory specified separately, worldwide English is a negotiation, not an assumption |
| Formats and channels | Explicit own-store permission; downloads, browser reading, other retailers, subscriptions, print, and audio addressed separately |
| Term | Bounded initial term; 24 to 36 months is a discussion range |
| Exclusivity | Limited to language, format, territory, and term needed to justify investment |
| Production process | AI use disclosed; approved vendors; review standard; no training or unrelated reuse |
| Editorial control | Approved style, honorific policy, and glossary; final proof, turnaround, significant changes, dispute handling |
| Artwork | Permitted lettering, sound-effect treatment, redraws, and cover adaptation; originals preserved |
| Money | Royalty basis, tax treatment, refunds, deductions, reserves, statements, currency, payment dates |
| Advances and guarantees | Recoupability, non-returnability, recoupment pool, any minimum guarantee |
| Attribution | Creator, translator, editor, letterer credits; contributor permissions |
| Publication and reversion | Deadlines, non-exploitation, expiry, renewal, existing-buyer treatment |
| Sequels | Bounded option or first discussion on named later volumes with a decision deadline |
| Corrections | Routine defects separated from material rewrites; version and approval records kept |
| Audit and disputes | Rights warranties, proportionate remedies, reporting inspection, agreed claims process |

The worked economics use a 50% rights-holder share of defined net receipts. That is a deal assumption, not a prescribed rate. When the licensor is a publisher, describe payment as a rights-holder share unless the creator's pass-through is verified.

### 3.5 Reader-informed commissioning

Keep a demand queue, but separate interest from authorization. Readers can request a title without a promise of publication. Use the states **requested → rights discussion → licensed → sample approved → commissioned → in production → approved → released**. Do not take money on an unlicensed title and call it a vote.

---

<a id="reader-experience"></a>
## 4. Reader experience and offers

### 4.1 The purchase journey

A reader arrives through a creator, a genre community, a permitted campaign, or title search. The landing page opens a substantial sample in the browser reader without account friction. It states language, page count, creator, series position, availability, review process, price, and access conditions. After payment, the reader gets the exact approved volume and a clear support route. The next interaction is a related available volume, a permitted sequel notice, or a correction to a purchased volume.

### 4.2 Title-page requirements

| Element | What the reader learns |
|---|---|
| Cover and hook | What kind of story it is |
| Description | Premise and stakes, without invented awards or endorsements |
| Catalog context | Genre, creator, series order, complete/ongoing status |
| Sample | Voice, dialogue, lettering, and reading comfort |
| Edition information | AI use, actual human review, translator and letterer credits |
| Format | Browser reader and any downloadable file; tested devices |
| Price | Correct total price for the buyer's country |
| Access | Hosted access versus download, account requirements, limitations |
| Support | Delivery help, defect reports, withdrawal where applicable, refunds, corrections |
| Next volume | A relevant available purchase, not an uncontracted promise |

Sell without AI in the headline, but show production disclosures before purchase. Say "fully reviewed" only when that review happened.

### 4.3 Proposed offers

| Offer | Planning treatment | Boundary |
|---|---|---|
| Authorized sample | Free | Permission for the sample and promotional assets required |
| Complete volume | €7.99 worked example, comparable to the US$8.99 J-Novel Club manga reference [R48] | One stable edition; price shown in the buyer's currency needs its own configuration |
| Three-volume collection | €19.99 modeled as a later option | Rights and title-level receipt allocation must permit it |
| Licensed reader-funded volume | Later, with published price, threshold, and delivery terms | Not part of the first checkout |
| Membership | Later, after catalog depth and repeat behavior justify it | No promise of unlimited translation on request |

### 4.4 Delivery

Provide a tested browser reader with right-to-left direction, correct page order, spreads, zoom, keyboard access, and resume. Supply downloadable files only where the license and the accessibility strategy support them.

Downloads and indefinite hosted access are different promises. Do not say "yours forever" when the agreement supports only revocable hosting. Negotiate and explain what buyers keep when sales stop or the license expires.

### 4.5 Retention starts with the next volume

Offer a clear series sequence. Measure second purchases only when a second volume was available in the window. Track repeat contribution, not email opens. Keep optional release notices separate from transactional messages.

### 4.6 Direct-first, not direct-only

Direct sales teach the most about samples, checkout, delivery, support, and repeat orders. Other retailers can be complementary when contracts permit. Check each retailer's exclusivity terms before combining them with direct sales.

---

<a id="competition"></a>
## 5. Competition

### 5.1 Compete for a complete reading outcome

| Alternative | Evidence | Implication |
|---|---|---|
| **Established English manga publishers and official simulpub apps** | Not in the research record; general market knowledge | They hold the major series. Compete on titles they have not licensed, not on their catalog. Research them before outreach. |
| **J-Novel Club** | Translated manga, previews, individual purchases, memberships, download policies. [R04] [R48] | Learn from catalog identity, samples, series cadence, and the prepublication-versus-final distinction. |
| **emaqi / Orange** | Licensed manga subscription in the US and Canada; company site did not reconfirm production scope. [R50] [R69] | Integrated localization plus distribution is a live competitor. |
| **Mantra** | Manga translation, typesetting, editing, and human-assisted services. [R45] | A production benchmark. Compare a complete volume, not a feature list. |
| **GlobalComix / INKR** | Opt-in localization, rights-holder control, retained art, human translators and letterers. [R46] | Creator control and human review are not unique. |
| **WEBTOON CANVAS** | Optional translation program, staged 2026 rollout. [R47] | Platform-native creators have alternatives. |
| **viviON Translators Unite** | Authorized, sales-linked translation; rejects machine translation; restricts external resale. [R49] | Creators already accept revenue-share translation; the source ecosystem is not inventory. |
| **Comic Translate** | Open-source detection, OCR, inpainting, translation, rendering. [R68] | The free baseline for page automation. Value must exceed it. |
| **Amimaru** | Human agency: translation, lettering, page QA. [R70] | Possible supplier or partner, not only a competitor. |
| **Existing licensed editions and other entertainment** | Checked title by title | The strongest competitor may be an ordinary volume already on sale. |

Product descriptions are first-party claims. No comparative quality result has been established.

### 5.2 The position

> **A trusted home for manga that deserves an English audience, supported by whole-volume localization and accountable editorial production.**

The reader-facing advantage must be visible in title relevance, samples, complete volumes, a good reader, and reliable releases. The production advantage must be visible in accepted output, editorial time, continuity, and a clean letterer handoff. These are commitments to validate.

### 5.3 Technical evidence

Context-informed manga translation research covers visual context, unit size, and context length. The Manga Whisperer covers panel and text detection, reading order, and speaker association. OnomatoBridge is a September 2026 preprint on sound-effect translation and rendering. These inform experiments; they do not establish publication quality for this implementation or license any manga. [R42] [R43] [R44]

### 5.4 A fair study

Use the same authorized volumes, comparable inputs, a defined final quality bar, and complete human-time accounting. Compare a strong general-purpose model workflow, a competent conventional process, and at least one specialist offering. Mark findings as demonstrated, documented, claimed, or unknown.

---

<a id="product"></a>
## 6. Production workflow

### 6.1 Three surfaces, one controlled edition

The **reader surface** is catalog, sample, checkout, delivery, access, and support. The **rights surface** is the evidence and permission record. The **editorial surface** is the whole-volume production and approval workflow. Rights negotiation, editorial allocation, and release approval can stay manual in the pilot.

### 6.2 Requirements

| Capability | Minimum useful outcome |
|---|---|
| Authorized intake | Exact source revision, rights basis, permitted vendors, scope, publication responsibility recorded |
| Import | Ordered PNG/JPEG pages, stable page and region IDs, confirmed right-to-left order, spreads, immutable originals; supplied scripts and clean art accepted |
| Preflight | Page count, density, unsupported material, asset quality, expected complexity visible before spending |
| Extraction | Editable regions, independent transcription, reading order, speaker suggestions |
| Difficult content | Visible handling for vertical text, handwriting, furigana, captions, signs, off-bubble dialogue, missed regions |
| Whole-volume context | Inspectable characters, aliases, voices, honorific policy, forms of address, recurring gags, terminology, source evidence |
| Translation | Scene-aware dialogue with explicit uncertainty and alternatives for ambiguous or constrained regions |
| Human-script entry | A supplied translation uses the same review and production workflow |
| Fit | Actual font rendering inside region geometry, minimum readable size, line breaks, overflow flags |
| Artwork | Changes confined to approved masks or explicit human work; originals recoverable |
| Review | Page view linking transcription, translation, speaker, evidence, fit, and approval |
| Controlled revisions | Regeneration proposes changes; accepted human edits are never silently overwritten |
| Quality assurance | Omissions, additions, inconsistency, unsupported clarification, and formatting triaged |
| Handoff | Stable script, proof images, glossary, and one editable lettering export tested by the actual letterer |
| Versioned export | Reproducible deliverables with immutable source and approval history |
| Release gate | Rights, editorial, file, price, territory, and delivery checks authorize the exact public edition |
| Accounting | Production cost, transactions, fees, taxes, refunds, royalties, and payments reconcile |

A character count is a prefilter, not a typography test. Prefer better phrasing and line breaks before shrinking text. Difficult sound effects, redraws, and artwork-dependent lettering stay explicit human tasks until automation is justified.

### 6.3 Whole-volume and series memory

Build a source-linked story bible before full production. Separate source facts, model inferences, and approved English choices. Each entry has scope, evidence, version, approval status, and narrative timing.

Distinguish what is true, what a character knows, and what the system knows after reading the whole volume. A late revelation may resolve ambiguity without being disclosed early. Store approved voice examples and specific decisions, not adjectives. For recurring jokes, record setup, payoff, English choice, and rationale. For honorifics and forms of address, record the policy and its exceptions.

Reuse approved series context through an explicit import and reconciliation step. Do not rewrite published volumes because a later one adds a fact. Glossary export must be portable.

### 6.4 Editorial responsibility

Require full bilingual review, lettering review, and artwork-integrity checks for every commercial volume. Creator approval is not bilingual quality assessment. A creator who does not read English may approve publication and terms without being represented as the English reviewer.

The workflow must expose ambiguity rather than hide it behind fluent output. Model explanations are editorial aids, not evidence of correctness. Readers get a correction route, but they are not unpaid first-pass QA for a product sold as reviewed.

---

<a id="architecture"></a>
## 7. Architecture and data

### 7.1 Reference architecture

```text
Reader catalog, reader, checkout      Rights and editorial workspace
             │                                    │
             └──────────── Application ───────────┘
                               │
               Work, rights, budget, source records
                               │
                    Durable production workflow
                               │
              Pages, regions, speakers, transcription
                               │
        Evidence-linked context → Translation → Checks → Repairs
                               │
                 Accountable human editorial review
                               │
                    Typography and lettering handoff
                               │
                Immutable, approved edition package
                               │
           Rights + quality + offer + delivery release gate
                               │
       Store → Payment → Entitlement → Delivery → Royalty ledger
                               │
               Corrections and next-volume production
```

A modular application, relational database, object store, and worker queue are enough. This is a responsibility model, not a microservices requirement. Hosted checkout may replace parts of the implementation once its behavior is tested.

### 7.2 Data model

| Entity | Responsibility |
|---|---|
| `Work` / `Series` | Original title, creators, series order, rights-holder identity |
| `DemandSignal` | Requested title, channel, consent, evidence; not a sale or license |
| `RightsGrant` | Exact edition, territories, formats, channels, term, exclusivity, processing permissions, approval rules, evidence |
| `SourceRevision` | Immutable source hash, page list, parser version, original asset references |
| `ProductionProject` | Reviewers, letterer, budget, scope, deadlines |
| `ContextRevision` | Source-linked characters, terminology, voices, honorific policy, chronology, accepted decisions |
| `Page` / `Panel` / `TextRegion` | Geometry, order, speaker proposals, transcription, masks, layout constraints |
| `TranslationUnit` | Source mapping, dependencies, drafts, configuration, cost, state |
| `Issue` / `ReviewDecision` | Location, category, severity, evidence, proposed repair, accountable reviewer, outcome |
| `EditionRevision` | Accepted pages, exported artifacts, metadata, credits, review record, release permission, rights reference |
| `Offer` / `PriceSchedule` | Edition, country, currency, tax classification, price, access terms, effective dates |
| `Order` / `Entitlement` | Transaction, purchaser, exact edition, delivery permission, refund/withdrawal status, access scope |
| `RoyaltyLedger` | Contract version, calculation basis, reversals, advances, reserves, accruals, statements, payments |
| `ExportManifest` | Input hashes, rendering parameters, output versions, handoff, reproducibility record |

Demand, source possession, completed translation, editorial acceptance, and sale permission are different facts. No valid release permission means no sale, even when export succeeded.

### 7.3 Job lifecycle and controlled changes

Production advances through preflight, context preparation, representative sample, full translation or script import, checks, targeted repairs, human review, lettering handoff, export, and release. Store intermediate artifacts so jobs resume and failures do not destroy approved work.

Use bounded retries, explicit cancellation, spending caps that include in-flight work, and escalation after a maximum repair count. A changed glossary creates an impact list and proposed edits, not a blind rewrite. Payment webhooks must be idempotent.

### 7.4 Model use

Condition translation on the scene, the page image, approved terminology, voice, honorific policy, house style, and retrieved evidence. Compare local, long-context, and structured-memory approaches before choosing the default. Add stronger-model escalation, cheaper routes, or fine-tuning only after an observed deficiency and measured benefit. Count every pass, retry, check, repair, and export. Saving tokens is not success if it adds paid editorial hours.

### 7.5 Security and data boundaries

Treat source material as untrusted data, not instructions. A fictional command cannot authorize tool calls, publication, payments, or disclosure. Limit worker permissions and network access, validate uploads, sanitize archives, redact logs, and test cross-project isolation. Preserve originals, keep audit logs, and implement the agreed retention and deletion process. No-training and approved-vendor commitments must match actual provider contracts and account settings.

### 7.6 Release and financial integrity

Deliver stored approved files; never regenerate a purchased volume at request time. Corrections create a versioned edition with an accountable decision and an update policy. Use deterministic code and ledgers for prices, tax, refunds, royalties, advances, and payouts. Model output never determines payable amounts. Reconcile each payment to its offer, edition, entitlement, tax treatment, and contract.

---

<a id="mvp"></a>
## 8. MVP and release gates

### 8.1 Minimum viable product

**Publish and sell one complete licensed English manga volume through a dependable reader journey, using a production process that can deliver the next volume.**

| Boundary | Initial commitment |
|---|---|
| Reader | One identifiable English-language manga readership |
| Language pair | Japanese to English only |
| Format | Page-based black-and-white manga volume, normally around 200 pages |
| Rights pipeline | Up to three candidate volumes from at least two rights holders |
| Production investment | Funding and capacity for two volumes, released sequentially |
| Source | Rights-holder-supplied ordered pages; frozen revision; scripts and clean art accepted |
| Review | Full bilingual review, lettering review, artwork-integrity check, licensor approval |
| Reader deliverable | Tested browser reader; downloadable file where licensed; licensed cover and metadata |
| Commerce | Catalog, sample, correct offer per country, payment, entitlement, delivery, support, optional notices |
| Accounting | Volume-level production cost; reconciliation of sales, taxes, fees, refunds, royalties |

### 8.2 Release gates

| Gate | Required evidence |
|---|---|
| Authorization | Rights chain and grant cover processing, production, promotion, territory, format, channel, delivery |
| Source coverage | Every narrative text region has an approved translation or an intentional editorial treatment; nothing disappears |
| Editorial quality | Promised review completed; critical defects resolved; public review claims accurate |
| Page quality | No known clipping, minimum-size violations, or unauthorized artwork changes; letterer round trip completed in the real workflow |
| Reader delivery | Reader and any file pass direction, order, spread, zoom, accessibility, entitlement, and version checks on real devices |
| Commercial offer | Correct seller, price, tax configuration, territory, access terms, disclosures, consent |
| Payment and delivery | A genuine order receives the correct edition; failed and duplicate events behave safely |
| Support | Delivery help, defects, withdrawal where applicable, refunds, corrections, records operational |
| Financial reconciliation | Order, receipt, tax, fees, reversals, royalty accrual, cash movements reconcile |

A clean proof inside the editor is not enough. Before the first sale, complete an authorized end-to-end production on a representative volume where the editor corrects regions, transcription, order, speakers, glossary, and translations, and the letterer opens, edits, and returns the handoff.

### 8.3 What may stay manual

Founder-led onboarding, rights negotiation, permission collection, uncertain speaker assignment, glossary approval, complex lettering, editorial review, final release, refunds, and royalty statements. Each needs an owner and recorded labor. Hidden manual work is an economic error.

### 8.4 Explicitly deferred

Reader uploads, arbitrary source downloading, scanlation marketplaces, other languages, vertical webtoon production, color volumes, native apps, live translation while reading, personalized editions, social feeds, character chat, audio, print, unlimited subscriptions, automated retailer submission, custom foundation models, autonomous publication, and any software offer to publishers.

### 8.5 Definition of done

A licensed volume passed the production and editorial process; accepted files are immutable and traceable; the title page is accurate; purchase and delivery work; the reader can get help; the company can reconcile money and partner obligations. Test payments prove function. Independent purchases prove a demand signal. Repeat production and repeat purchases decide further investment.

---

<a id="quality"></a>
## 9. Quality evaluation

### 9.1 Evaluate the volume readers receive

The core metric is total cost to an agreed editorial standard per accepted volume, paired with serious-error outcomes, complete human effort, reliable files, and reader experience. Measure the automated draft and the finished reviewed volume separately, or the platform will claim editorial work as a model improvement.

### 9.2 Corpus and baselines

Evaluate at least three complete permissioned volumes with different difficulty profiles, one held out from prompt and rule tuning, plus a continuation test that reuses approved series context. Compare a competent existing production process with the assisted workflow. Ablate local context, whole-volume context, and structured memory on the same model. [R42] [R43]

### 9.3 Metrics and protocol

| Dimension | Measurement |
|---|---|
| Fidelity | Serious mistranslations, omissions, invented content, unsupported clarification, distorted characterization |
| Continuity | Names, terminology, relationships, honorifics, voice, recurring-joke decisions across distant pages |
| Reading | Dialogue, register, rhythm, ambiguity, comfort |
| Visual understanding | Missing regions, transcription errors, reading order, speaker attribution |
| Page fit | Overflow, minimum-size violations, line-break corrections, letterer intervention |
| Artwork integrity | Changes outside approved masks; recoverability |
| Checker usefulness | Consequential defects found, false positives, review time |
| Labor | Extraction repair, translation and editing, lettering, QA, rework |
| Delivery | Time to accepted export; real reader and file behavior |
| Reader outcome | Delivery problems, defects, refunds, enjoyment, subsequent purchases |
| Partner outcome | Approval time, accurate reporting, willingness to license the next volume |

Use paid bilingual assessors with a second reviewer for disputed judgments. Blind workflow identity where practical. MQM supplies an error-category framework; the manga protocol must be defined for this product. [R40] The volume, not thousands of correlated regions, is the unit for uncertainty. Monolingual satisfaction cannot certify fidelity.

### 9.4 Targets, not guarantees

Investigate 30% lower total production effort against a strong practical baseline as the initial target and 40% as a stronger result, without worse serious-error outcomes. Record which stages improve. A drafting-time gain can be outweighed by lettering, correction, or support. Do not promise percentages before measurement.

### 9.5 Public demonstration

Use a commissioned or explicitly authorized 24 to 40 page sample with recurring characters, a delayed joke payoff, changing forms of address, visual ambiguity, dense dialogue, irregular bubbles, and difficult lettering. Make the story engaging first, then show the work: an early reference and its later payoff, the source-linked decision, a targeted correction, preserved approved material, and the actual deliverable. End on the reviewed volume.

### 9.6 Corrections

A complaint triggers editorial assessment, not automatic rewriting. Material changes need the agreed approval and update process. Corrections must not erase purchase history or silently replace the reader's edition with a different style.

---

<a id="economics"></a>
## 10. Unit economics

### 10.1 Discipline

The company invests in approved volumes and earns reader contribution over their license terms. The next reader adds payment, service, and royalty cost, not a new translation. Keep catalog publishing and shared overhead in separate ledgers.

The worked case counts **gross orders** with an expected refund reserve. Actual reporting must reconcile gross orders, refunded value, retained orders, and net sales from the transaction ledger.

### 10.2 Production investment per volume

| Ordinary 200-page volume | Assumption | Amount |
|---|---|---:|
| Bilingual translation and editing | 18 hours × €40 | €720 |
| Lettering | 6 hours × €30 | €180 |
| Independent proof and QA | 4 hours × €40 | €160 |
| Compute, preparation, export | Allowance | €40 |
| Rights and asset coordination | Allocated labor | €150 |
| Sample, metadata, accessible-text preparation | Allowance | €150 |
| Rework contingency | Allowance | €100 |
| **Total production investment** | **Planning case** | **€1,500** |

Assumes a royalty-only license with no advance. Japanese-to-English literary rates may exceed €40 per hour; get quotes. Dense dialogue, retranslations, redraws, accessibility work, and slow approvals push a volume toward the €3,000 "demanding" sensitivity.

### 10.3 Per-order contribution: base case

Base case: a buyer outside the EU, price €7.99, no VAT deducted. US sales tax and UK VAT treatment are not established by the research basis and need an adviser before launch. EU buyers pay destination VAT; see the 9% sensitivity. [R24] [R59] [R60]

| Per gross €7.99 order | Amount |
|---|---:|
| Consumer payment | €7.99 |
| Expected refunds: 3% of sales | €0.24 |
| Payment fee: 2.5% + €0.25 | €0.45 |
| Defined net receipts | €7.30 |
| Rights-holder royalty: 50% of net receipts | €3.65 |
| Delivery and support | €0.20 |
| Dispute allowance | €0.05 |
| **Contribution before acquisition** | **€3.40** |
| Acquisition allocation per order | €1.50 |
| **Contribution toward production and overhead** | **€1.90** |

Net receipts deduct refunds and payment fees, not advertising, production, or overhead. The refund reserve is a planning device, not contractual permission to withhold royalties. The payment rate is deliberately above the researched Stripe standard EEA-card rate of 1.5% + €0.25; international cards and currency conversion will apply to most buyers. [R61]

Recovering a €1,500 volume needs **442 gross orders** before acquisition or **790** after it, before overhead.

| Gross orders | After acquisition and €1,500 production; before overhead |
|---:|---:|
| 100 | −€1,310 |
| 250 | −€1,025 |
| 500 | −€550 |
| 1,000 | €400 |
| 2,000 | €2,301 |

### 10.4 Sensitivities

| Case; base unless stated | Contribution per order | Production | Recovery orders |
|---|---:|---:|---:|
| €7.99; no acquisition allocation | €3.40 | €1,500 | 442 |
| €7.99; €1.50 acquisition | €1.90 | €1,500 | 790 |
| €7.99; €0.50 acquisition | €2.90 | €1,500 | 518 |
| €7.99; €3.00 acquisition | €0.40 | €1,500 | 3,748 |
| Demanding volume; no acquisition | €3.40 | €3,000 | 883 |
| Demanding volume; €1.50 acquisition | €1.90 | €3,000 | 1,579 |
| €5.99; no acquisition | €2.46 | €1,500 | 611 |
| €9.99; no acquisition | €4.35 | €1,500 | 346 |
| 60% rights-holder share; no acquisition | €2.67 | €1,500 | 562 |
| EU buyer at 9% VAT; no acquisition [R59] | €3.08 | €1,500 | 487 |
| EU buyer at 9% VAT; €1.50 acquisition | €1.58 | €1,500 | 950 |

Acquisition cost is the dominant lever. Compute savings cannot compensate for unplanned editorial hours or paid traffic that eats contribution.

### 10.5 Reader cohorts and collections

If every acquired reader buys one volume, 45% buy a second, and 25% a third, that is 1.7 expected orders per reader. At €3.40 contribution per order, €5 acquisition per new reader, and €0.20 retention cost per extra order, contribution is about **€0.64 per acquired reader** before production and overhead. Paid acquisition at €5 per reader does not work at this basket size. Readers must come from creator audiences, communities, and series continuation, or the basket must grow.

A €19.99 three-volume collection yields about **€8.87 per bundle order** before acquisition, production of all three volumes, and overhead. It raises basket size and lowers revenue per volume. Agree receipt allocation between titles and rights holders before offering it.

### 10.6 Advances, guarantees, and reserves

A recoupable advance offsets earned royalties; track advance paid, earned royalty, recoupment, and cash payable separately. A non-recoupable fee adds to fixed title cost. Cross-title recoupment needs express agreement. Tax, accrued royalties, processor reserves, and refundable funds are not spendable cash.

---

<a id="finance"></a>
## 11. Budget and cash

### 11.1 Operating budget

| Shared fixed allocation | Monthly |
|---|---:|
| Founder compensation allocation | €4,000 |
| Fractional product and frontend capacity | €2,000 |
| Recurring product and domain evaluation | €1,000 |
| Administration, security, bookkeeping, sales tools | €1,000 |
| **Total** | **€8,000** |

Volume production, advances, variable delivery, and payment costs sit outside this allowance. Real payroll, contractor, tax, and insurance costs replace the placeholders.

### 11.2 Ninety-day validation allocation

| Discretionary workstream | Allowance |
|---|---:|
| Two manga volumes at €1,500 | €3,000 |
| Authorized end-to-end pilot: extraction evaluation, letterer round trip, reader testing | €3,000 |
| Publishing/IP advice including Japanese title advice, consumer, and tax setup | €5,000 |
| Reader research and independent Japanese-English assessment | €3,000 |
| Storefront, browser reader, delivery, accessibility testing | €3,000 |
| English-reader acquisition experiments | €3,000 |
| Contingency and uncommitted third-volume reserve | €5,000 |
| **Discretionary validation envelope** | **€25,000** |
| Three months of shared operating budget | €24,000 |
| **Proposed 90-day allocation** | **€49,000** |

Book each invoice once. The allowance does not finance material rights advances, extensive redraws, or a second language.

### 11.3 Release capital in stages

First fund rights discussions, paid samples, reviewer and letterer quotes, and reader research. Then approve the first production budget and minimum commerce. Commit the second volume only within reserved capacity and in light of the first volume's evidence. Keep the third-volume reserve uncommitted until a specific case exists.

An illustrative €120,000 opening capital leaves €71,000 uncommitted after the €49,000 allocation, before revenue, taxes, liabilities, or further commitments. That is a subtraction, not a runway forecast.

### 11.4 Company-scale thresholds

Three volumes selling 1,000 gross orders each at €7.99 generate €23,970 in receipts and leave about **€1,200 after per-order costs, acquisition, and €4,500 production**, before overhead. Useful validation, not a business.

| Catalog profile | Contribution | Monthly spending to cover | Required gross orders |
|---|---|---:|---:|
| Existing backlist; no new production | €3.40 per order before acquisition | €8,000 | 2,353 |
| Same, with €1.50 acquisition per order | €1.90 | €8,000 | 4,210 |
| Backlist plus two new €1,500 volumes | €3.40 | €11,000 | 3,236 |
| Same, with €1.50 acquisition per order | €1.90 | €11,000 | 5,789 |

These are coverage tests, not forecasts. Release timing, backlist decay, seasonality, working capital, and capacity are not represented by one division.

### 11.5 Cash model

Build one linked monthly model with schedules for titles, license terms, production stages, cash commitments, orders by volume and country, tax, royalties, advances, refunds, acquisition cohorts, editorial capacity, and overhead.

```text
Company cash change
  = reader cash collected
  + expressly agreed partner funding
  − production and rights cash paid
  − transaction, delivery, support, and acquisition cash paid
  − tax and royalty settlements
  − shared fixed operating expenses
  − one-off setup commitments
```

For each volume model launch month, months two to six, later backlist, and license expiry. Include weak sequel conversion, several unrecouped volumes, slow licensor approvals, and higher-than-expected editorial work.

### 11.6 Investment discipline

Review cash, committed production, taxes, royalties, and refundable funds monthly. Below six months of modeled coverage, cut fixed commitments and uncommissioned volumes. The levers that matter are title-and-reader fit, repeatable low-cost acquisition, fewer costly editorial errors, negotiated terms, reliable releases, and repeat purchases.

---

<a id="legal"></a>
## 12. Rights, legal, privacy, and trust

### 12.1 The route is licensed publishing

Obtain the rights, publish within the grant, run a compliant consumer sale. Translation, adaptation, reproduction, and publication all need authorization under Berne and national law. Japanese title and contract advice is required for every acquisition. [R10] [R12] [R51]

The company is Dutch and sells English volumes to consumers in several countries. Incorporation, server location, and choice-of-law clauses do not replace review of each cross-border transaction. **The research basis covers EU consumer, tax, and accessibility rules. It does not establish US consumer, sales-tax, or UK VAT compliance.** Those are launch-blocking adviser tasks for the proposed first markets.

### 12.2 Four separate questions

| Question | Establishes | Does not establish |
|---|---|---|
| May the company obtain and process the source? | Authority to ingest assets and use specified providers | Permission to publish or sell |
| May it translate and publish? | Licensed exploitation in a defined language, format, territory, channel | Ownership of new contributions |
| What rights exist in the English edition? | Protection of qualifying human-created text, lettering, selection | Permission to exploit the original without authorization |
| May it make this consumer sale? | Valid offer, territory, term, price, delivery, disclosures, support | Permission for all countries, subscriptions, or future uses |

A model vendor's output terms cannot grant rights that belong to a creator, publisher, or translator. [R12] [R14]

### 12.3 Clearance by asset and use

Clear the artwork, source edition, any existing translation, scans, clean pages, cover, descriptions, promotional excerpts, fonts, and commissioned contributions separately. "Creator-owned" starts the check. The license must cover the actual pipeline: production copies, third-party processing, samples, finished files, direct sales, downloads or hosting, corrections, and access after termination. Express AI-processing terms clarify copying, vendor access, confidentiality, retention, and subcontracting. Verify providers' actual terms before promising no training or restricted retention.

| Proposed input | Basis to establish | Treatment |
|---|---|---|
| Rights-controlling creator supplies a volume | Chain of rights, third-party content, signed scope | Suitable after clearance |
| Publisher or agent supplies assets | Actual authority for language, format, territory, processing, sale | Suitable after review |
| Reader-purchased volume uploaded for translation | Source terms, exceptions, provider role, destination law | Outside the product; private-copying case law does not clear a commercial translation sale [R51] [R67] |
| Out-of-print or apparently abandoned series | Copyright status and actual permission | Lead, not inventory |
| Fan work using an existing franchise | Creator's contribution plus underlying franchise rights | Artist consent alone is insufficient |
| Text-only script or overlay | Translation and adaptation rights despite omitted art | Not a licensing workaround |

### 12.4 AI, research exceptions, and fair use are not catalog licenses

EU text-and-data-mining provisions cover analysis-related copying, not selling translated entertainment. Japan's official AI and copyright explanation distinguishes analysis or training from generation and public exploitation; it is expressly non-binding and dated. US fair use is fact-specific; a complete commercial translation serving the translated-reading market is not pre-cleared because a model produced it. [R14] [R55] [R57]

### 12.5 Creator contracts, moral rights, and contributors

Attribution and integrity protections can remain with a creator after economic rights transfer and cannot always be waived. Agree credits, permitted lettering and sound-effect treatment, redraws, cover adaptation, significant-change approval, and a dispute route. Contract with translators, editors, and letterers for the rights to publish, distribute, correct, and maintain their work. Payment alone is not evidence of transfer. [R11] [R13] [R51]

### 12.6 Copyright in the AI-assisted edition

US and Dutch guidance focus protection on sufficient human creative contribution; prompts alone do not establish authorship. Keep permission to exploit the original separate from protection of new wording. The edition has commercial value through its license, genuine editorial and lettering work, brand, catalog, and reader relationships even where protection of some generated text is uncertain. Avoid the claim that "human edited" means "fully copyrighted." [R41] [R56]

### 12.7 Price rules, tax, and payment operations

English-language editions sold to Germany or France may or may not fall under national fixed-price rules; check before offering discounts or bundles there. Dutch ebooks are outside the Dutch fixed-price requirement. [R20] [R21]

EU buyers pay destination VAT; the Netherlands applies 9% to qualifying ebooks and OSS simplifies reporting without creating one EU rate. Non-EU buyers need their own tax treatment established. Document seller identity, place of supply, buyer-location evidence, invoices, refund reversals, and royalty treatment with an accountant. Verify processor settlement, refunds, content eligibility, supported countries, reserves, disputes, and conversion fees. A processor is not automatically merchant of record. [R23] [R24] [R59] [R60] [R61]

### 12.8 Consumer contracts, withdrawal, and defects

Before purchase, show the seller, total price, language, complete/ongoing status, format, compatibility, access conditions, and support route. For EU buyers, immediate digital supply requires express consent and acknowledgment of the withdrawal consequence, recorded with timestamp and terms version, not a pre-ticked box. Withdrawal and conformity remedies are different: valid consent does not remove remedies for missing pages, unreadable files, or wrong-language supply. A free sample is not a waiver. [R25] [R26] [R27] [R58]

### 12.9 Preorders and reader-funded volumes

A nonbinding request can precede rights negotiation. A paid campaign cannot. Before collecting money, secure rights, define the edition and review scope, identify the seller, set threshold and deadline, and specify refund treatment if funding or production fails. The MVP sells completed volumes because that is the clearest fulfillment test.

### 12.10 Accessibility

EU accessibility requirements cover relevant ebooks and ecommerce from 28 June 2025, with exemptions that startup status and image-heavy content do not settle. Build logical reading order, zoom, usable dialogue text access, keyboard-accessible commerce, and an explicit accessible-content strategy for page images. A set of image files is not an accessibility plan. [R28]

### 12.11 AI transparency

Article 50 obligations apply from 2 August 2026 and distinguish provider duties from deployer disclosure. Map whether the company is provider, deployer, or both; do not assume an external API settles it. Disclose the actual process plainly: AI-assisted localization with identified human editorial and lettering work. [R31] [R63]

### 12.12 Privacy

Customer profiles, purchases, mailing lists, and contracts involve personal data. Establish purposes, lawful bases, roles, retention, security, processor agreements, and transfer safeguards. Separate fulfillment, accounting, editorial, support, and optional marketing. Do not send reader purchase histories into model prompts. Use limited aggregate analytics; tracking needs consent. [R33] [R34] [R62]

### 12.13 Expiry and existing buyers

Stopping new sales is not the end of obligations to buyers. Negotiate download permissions, re-download periods, hosting, corrections, and archival delivery after expiry. J-Novel Club's policy distinguishing retained downloads from re-download availability is an example, not a rule the company can adopt without agreement. Implement expiry alerts, approved territory lists, and controlled delisting that preserves tax and royalty records. [R04]

### 12.14 Legal release file

| Deliverable | Required before |
|---|---|
| Title-rights report: source, licensors, contributors, territories, formats, channels, term, authority | Processing and publication |
| Publishing agreement | Commercial commitment |
| Contributor, asset, and font clearances | Use in samples or editions |
| Verified vendor and data-flow pack | Proprietary uploads and customer data |
| Approved seller, tax, price, consumer, consent, and remedy configuration per launch country | Live checkout |
| Accessibility scope assessment and reader testing | Public release |
| Editorial and licensor approval; signed release manifest | Sale of the exact edition |
| Exit and incident runbook: defects, claims, delisting, prior buyers, refunds, royalties, deletion | Launch |

---

<a id="go-to-market"></a>
## 13. Go-to-market

### 13.1 Acquire readers through a title

The first campaign promotes a specific volume to a specific English-language manga audience: the creator's existing English-speaking followers, a genre community that permits promotion, a newsletter or creator partnership, and title-specific search. Measure founder time, partner fees, campaign assets, and failed experiments. "Organic" is not free.

The first proof is a reader who pays, enjoys the volume, and buys the next one, while the rights holder is satisfied with production, reporting, and payment.

### 13.2 Initial experiments

| Experiment | Execution | Evidence |
|---|---|---|
| Authorized sample launch | One volume, substantial sample, correct price per country, documented traffic | Conversion, disclosure comprehension, delivery success, refunds |
| English reading group | Paid or permissioned recruitment; disclosed advance copies; no required positive reviews | Enjoyment, defects, reasons to buy or decline, later independent purchases |
| Next-volume offer | Available volume two under proper marketing permissions | Second-purchase rate, timing, contribution, retention cost |

Do not merge review copies, paid participants, internal payments, refunds, and genuine orders. At 3% conversion and €5 per first buyer, traffic can cost only €0.15 per qualified visit. That is why creator and community partnerships matter more than paid ads.

### 13.3 Outreach seed register

Public routes from the 22 September 2026 research. All are prospecting leads, not warm introductions, rights offers, or endorsements. No outreach has been sent.

| Organization | Role and route | First ask | Qualification |
|---|---|---|---|
| **J-Novel Club** | Publisher; `contact@j-novel.club` | Route a title-specific rights or partnership discussion to the right team | Competitor and possible partner; no catalog access assumed. [R71] |
| **TOKYOPOP** | Publisher; `info@tokyopop.com` | Identify the team for one bounded backlist or series evaluation | Confirm business unit and market. [R74] |
| **Amimaru** | Localization agency; `sales@amimaru.com` | Bounded production partnership for lettering or QA | Supplier, partner, or competitor; define data ownership. [R70] |
| **viviON Translators Unite** | Creator ecosystem with authorized translation | Learn how creators there think about licensed English editions | Not inventory; rules reject machine translation. [R49] |
| **Mantra** | Production competitor | Benchmark only | No partnership assumed. [R45] |
| **MQM Council** | Evaluation framework | Assessor referrals or methodology guidance | Not an acquisition channel. [R40] |
| **Japanese indie creators and small publishers** | Official business contacts, verified title by title | Who controls the English digital rights; may a licensed pilot be discussed? | Requires Japanese-language outreach; no creator qualified yet |
| **English literary translator associations** | Not in the research record | Willing paid Japanese-English reviewers and independent assessors | Establish suitability and rates individually |
| **English manga communities and reviewers** | Not in the research record | Requirements, fees, and AI-content policy for a disclosed reading group | Campaign acceptance unknown |

### 13.4 Rights-partner discovery

Ask about the rights chain, prior grants, options, source-file quality, existing English editions, AI policy, approved vendors, sample permission, editorial approval, direct-sale rights, sequel access, and minimum financial expectations. The next step is a paid or permissioned sample and a scoped term discussion, not an unsolicited public translation.

### 13.5 Measurement

Track contact source, role, title fit, rights authority, AI policy, next action, owner, and status. For every reader channel record exposures, qualified visits, sample starts and completions, orders, refunded value, retained customers, cost, and subsequent orders, with denominators and attribution windows.

---

<a id="roadmap"></a>
## 14. Roadmap and decision gates

### 14.1 First twelve weeks

A proposed sequence, not a release date. Rights negotiation, editorial capacity, and sample findings set the timing.

| Period | Reader and commercial | Rights and production | Product and operations |
|---|---|---|---|
| **Weeks 1–2** | Interview English manga readers; define the catalog promise and discovery routes; source a market measurement | Qualify rights holders in Japanese; get translator and letterer quotes; shortlist up to three volumes | Page import, preflight, title-page prototype, rights and evidence records |
| **Weeks 3–4** | Test permitted samples and price presentation per country; identify the first audience | Negotiate the first license; freeze source, review scope, sample style, honorific policy, production budget | Durable production stages, whole-volume context, protected edits, extraction on real pages, cost tracking |
| **Weeks 5–8** | Prepare the launch channel and support | Complete volume one: full review, lettering round trip, approvals; start volume two only within reserved capacity | Browser reader, checkout per launch country, delivery, refund flow, entitlement and ledger tests |
| **Weeks 9–12** | Sell volume one; analyze channel costs and support; offer volume two when ready | Review actual economics; decide the second and third commitment | Fix observed failures; document release operations; measure repeat purchases |

### 14.2 Continuation gates

| Gate | Evidence sought | Response when weak |
|---|---|---|
| Rights supply | Two qualified relationships and a workable first agreement | Narrow the catalog or change recruitment; never replace licensing with uploads |
| Production delivery | Full review, letterer round trip, no critical defects, actual cost recorded | Fix error categories or re-scope |
| Reader operations | First 10 independent orders delivered and supported | Repair checkout and delivery before promotion |
| Initial demand | 50 to 100 gross orders with a known acquisition denominator | Reassess title, audience, sample, channel, or price |
| Title recovery | A recovery trajectory inside the license term | Cap new commitments |
| Repeat value | Second purchases when volume two is available | Improve catalog fit and cadence before membership |
| Trust and compliance | Permissions, disclosures, tax, prices, delivery, support, data controls work in each launch country | Keep the affected market closed until resolved |

Set windows and thresholds before experiments. Small numbers teach; they do not prove profitability.

### 14.3 Expansion order

Improve volume one's production and acquisition. Release volume two and test the second purchase. Add a compatible series from another rights holder. Then, in order and each on its own case: a three-volume collection, reader-funded volumes, membership, additional sales countries, color or webtoon formats, and only much later a second target language.

### 14.4 Milestones

1. A complete accepted volume and an independent purchase.
2. A second purchase and a repeatable production.
3. Positive contribution with bounded support and a credible recovery path.
4. One validated expansion axis: another series, a collection, or a new market. Not all at once.

---

<a id="operations"></a>
## 15. Team and operations

### 15.1 Initial team

The founder covers ML and backend, product ownership, and part of commercial development. Add fractional product and frontend support for the reader and checkout, a senior Japanese-English translator or editor, an English letterer, an independent assessment route, and paid legal, tax, and accessibility expertise. Japanese-language business capability is needed for outreach and contracts.

Assign rights acquisition, editorial acceptance, reader support, price and tax configuration, royalty reporting, privacy, accessibility, and expiry management explicitly. The founder should not be the sole judge of fidelity, contract sufficiency, and demand.

### 15.2 Weekly review

Review title opportunities, rights status, budgets, production blockers, editorial capacity, releases, reader cohorts, refunds, partner liabilities, and runway together. For each job: was the output accepted, where did human time go, what did delivery cost, what would make the next volume easier? Record time during delivery.

### 15.3 Documentation and owners

| Deliverable | Owner and timing | Content |
|---|---|---|
| Venture and customer brief | Founder; weeks 1–2 | Reader, catalog, offer, economics, exclusions, evidence gaps |
| Title-selection and rights register | Commercial owner and counsel; before processing | Availability, authority, source, grants, vendors, term, proof |
| Publishing agreement template | Counsel; before commitment | Scope, royalties, approvals, data, assets, publicity, expiry, disputes |
| MVP and UX specification | Product and editorial; weeks 1–4 | Journeys, states, editable objects, input limits, manual tasks, done |
| Architecture and API contracts | Engineering; weeks 1–4 | IDs, jobs, authorization, versioning, retries, budgets, release boundary |
| Editorial playbook | Senior translator; before production | Samples, context, honorific policy, review, escalation, credits, corrections |
| Typography and lettering contract | Letterer and engineering; before the pilot | Fonts, geometry, readable size, line breaks, SFX exceptions, round trip |
| Evaluation protocol | Editor, ML, independent assessor; before held-out testing | Corpus, baselines, severity, assignment, uncertainty, targets |
| Vendor, security, privacy pack | Engineering and counsel; before private processing | Roles, access, data flow, transfers, retention, incidents, deletion |
| Consumer and pricing configuration per country | Commercial owner and advisers; before checkout | Seller, prices, tax, terms, consent, delivery, remedies, support |
| Accessibility checklist | Product and specialist; before release | Scope assessment, reader tests, unresolved defects |
| Financial and capacity model | Founder; before spending | Volume investment, labor, acquisition, royalties, advances, cash |
| Royalty and transaction ledger | Finance owner; before first sale | Contracts, receipts, tax, fees, reversals, accruals, statements, payouts |
| Release and incident runbooks | Engineering and operations; before launch | Gates, failures, rollback, defects, refunds, claims, delisting |
| Expansion decision memo | Founder; after first cohort | Quality, recovery, repeat purchases, rights supply, costs, next step |

### 15.4 Foundations and funding

Resolve ownership, founder arrangements, contractor IP, bookkeeping, banking, contract authority, and insurance before substantial proprietary material. Keep an evidence ledger: claim → source or experiment → date → limitation → affected decision.

Rights and editorial costs precede sales, so the catalog needs working capital from capped founder or seed funding, or negotiated co-funding. Do not build a large speculative catalog because generation is cheap.

---

<a id="risks"></a>
## 16. Risks and open decisions

### 16.1 Risk register

| Risk | Early signal | Response |
|---|---|---|
| Major titles are unavailable | Every wanted series is already licensed by an established publisher | Focus on creator-owned, small-publisher, and backlist titles with proven niche demand |
| Demand is fragmented | Many requested titles, few buyers per volume | Concentrate on one readership and license coherent clusters |
| Acquisition eats contribution | Sales stop when paid promotion stops | Creator and community channels; measure all acquisition work |
| Rights do not fit | Direct sales, AI processing, territory, or hosting excluded | Negotiate the actual use or pick another title |
| Sequel access fails | Readers cannot buy volume two | Bounded sequel arrangements; accurate status |
| Fluent text hides errors | Bilingual review finds omissions or changed plot | Source mappings, targeted checks, full review |
| Automation shifts work to the letterer | Overflow, order errors, redraws dominate | Improve the handoff; quote complexity honestly |
| Review exceeds budget | Sample estimates diverge from whole-volume hours | Re-scope; use actual cost for the next commitment |
| Tax or consumer rules wrong by country | Checkout, tax, or consent behave inconsistently | Adviser-approved configuration per launch country; close markets that are not ready |
| Output ownership overstated | Contracts promise protection unsupported by authorship | Separate license, human contributions, and uncertain output rights |
| Vendor commitments fail | Retention, training, or content policy conflicts | Verify contracts and settings; keep approved alternatives |
| Reader trust erodes | Vague review labels, poor delivery, unresolved defects | Provenance, support, and corrections are part of the product |
| Expiry breaks promises | Sales continue after rights end | Expiry alerts, surviving permissions, controlled delisting |
| Scope creep | Features grow while licensed volumes and sales do not | Return to the next accepted volume and next order |
| Cash looks healthier than it is | Tax, royalties, refunds treated as free cash | Reconcile liabilities before spending |

### 16.2 Decisions before the first commitment

- First sales countries and their tax and consumer configuration.
- Operating entity, responsible translator and letterer, production quote, funded budget.
- Per title: source and asset rights, term, exclusivity, royalty basis, advance, approval, launch channel, sequel access, corrections, prior-buyer treatment.

The plan does not invent an available title, a signed licensor, a willing reviewer, or a market measurement.

### 16.3 Distinguish failure modes

A weak title does not disprove the production engine. An excellent translation does not prove demand. Separate title selection, audience reach, price, quality, delivery, and unit economics when deciding what to change. Improve typography when lettering dominates; improve rights recruitment when approvals stall; improve catalog fit when repeat buying is weak.

---

<a id="sales-materials"></a>
## 17. Sales and partnership materials

Prelaunch drafts. Use availability, prices, named reviewers, and delivery promises only when the rights, production, and operations are ready.

### 17.1 Reader landing page

> # Your next favorite manga might be waiting in Japanese.
>
> Discover manga selected for readers like you, brought to English with the permission of the people who created it.
>
> Read a substantial sample. Get to know the world, the characters, and the voice. Then buy the complete volume and keep reading.
>
> **More manga. One clear purchase.**
>
> No credits to count. No uploads. No membership required for individual volumes. Each title shows its page count, price, credits, and access conditions before you buy.
>
> **The same story. A new audience.**
>
> We use story-aware production tools alongside human translation, editing, and lettering. Meaning, character voice, continuity, and every page are reviewed. The title page explains the work done on that volume.
>
> **Published with permission.**
>
> Every volume is licensed from its creator or rights holder, who receives the agreed share of sales. We credit the people responsible for the original and the edition you read.
>
> **Help shape the next release.**
>
> Tell us which series you want in English. A request is not a payment or a promise of publication.
>
> **Read a sample** · **Explore available manga**

### 17.2 Title-page copy

> **[Title]: a new story to get lost in. Now in English.**
>
> [Accurate, story-led premise and why it fits the reader.]
>
> Read the opening sample before you buy. This is the complete, authorized English edition, produced with AI-assisted localization and [precise description of the completed bilingual review and lettering].
>
> **Read the sample** · **Buy the volume — [price in the buyer's currency]**
>
> [Format, tested devices, credits, seller, access conditions, support.]

Do not fabricate endorsements, awards, ratings, or sales.

### 17.3 Rights-holder email

Send in Japanese where the recipient works in Japanese; the English draft is the reference text.

**Subject: English digital publishing rights for [Title]**

> Hi [Name],
>
> We are building a specialist catalog for English-language readers who want more [specific genre] manga. We license selected works, organize translation, lettering, and complete editorial review, and sell the finished volumes directly to readers.
>
> [Title] could fit because [specific, verified reason]. For a pilot, we would agree a narrow format, territory, and term; your approval process; an explicit AI-processing policy; artwork and lettering rules; and transparent royalty reporting. We fund the production.
>
> The first step would be one volume and a permitted sample. Do you control the English digital rights, or could you direct me to the person who does?
>
> [Name / company / business contact]

### 17.4 Reader community or reviewer message

> We are preparing an authorized English edition of [Title], a [genre] manga about [accurate premise]. We are looking for a relevant reading group or clearly disclosed promotion, not general AI publicity.
>
> We can provide a permitted sample and describe the translation and human review accurately. What are your requirements, fees, and policy on AI-assisted editions? Reviews stay independent, with compensation or free copies disclosed.

### 17.5 Reader FAQ

**Do I need a subscription?** No. The first offer is individual complete volumes.

**Are these authorized translations?** The store sells only volumes licensed from the rights holder. Each release names the creator and licensor.

**Do you use AI?** The workflow uses AI-assisted localization with human translation review, editing, and lettering. The edition page says what was done and who was responsible.

**Can I download the volume?** Access conditions appear before purchase. Every volume reads in the browser; downloads are offered where the license permits.

**Can I request a title?** Yes. A request is not a grant of rights or a guaranteed release.

**Can I upload manga for translation?** No. The store sells a selected licensed catalog.

**What if I find an error?** Use the report-a-problem route. Issues get editorial assessment, correction where appropriate, and applicable remedies.

**What happens when a title leaves the store?** The edition's terms say what buyers keep. Download and re-download permissions are agreed with the rights holder before sale.

### 17.6 Marketing checklist

Confirm title rights, features, formats, capacity, price per country, tax, reviewer identification, royalty statement, and delivery date before any claim. Do not claim every title, permanent hosted access, 100% human translation, or no refunds unless the facts and rules support the exact statement. A 50% share of net receipts is not 50% of the consumer's payment.

---

<a id="conclusion"></a>
## 18. Immediate priorities

The company is a manga publisher with a production platform, not a translation endpoint looking for a market. Its promise is more compelling manga for English readers through complete, authorized, dependable volumes.

Next steps, in order:

1. Source a measurement of the English digital manga market and a list of specific unlicensed titles with named demand.
2. Confirm tax and consumer configuration for the first sales countries with an adviser.
3. Open Japanese-language rights conversations with creator-owned and small-publisher titles; obtain permitted samples.
4. Get translator and letterer quotes; run the paid sample assessment and the end-to-end pilot with a real letterer round trip.
5. Sign one volume, produce it, sell it through a creator or community channel, and use the evidence to commission volume two.

> **Translate with context. Publish with permission. Earn the reader's next volume.**

---

<a id="financial-appendix"></a>
## Appendix A. Financial formulas

### A.1 Conventions

Amounts are EUR. The base case deducts no VAT (buyer outside the EU); the EU sensitivity uses 9% Dutch VAT. A gross order includes orders that may later be refunded; the 3% reserve is a share of sales value. A recovery threshold is the smallest whole number of modeled orders whose contribution covers the stated investment. It is not a forecast or a company break-even.

### A.2 Per-volume formulas

```text
GrossPrice = 7.99
VATRate = 0.00                  # base; 0.09 for the EU sensitivity
RefundRate = 0.03
PaymentRate = 0.025
FixedPaymentFee = 0.25
RoyaltyShare = 0.50
DeliverySupport = 0.20
ExpectedDisputeCost = 0.05
AcquisitionPerOrder = 1.50
TitleProduction = 1,500

ExVAT = GrossPrice / (1 + VATRate)
ExpectedRefunds = ExVAT × RefundRate
PaymentFees = GrossPrice × PaymentRate + FixedPaymentFee
DefinedNetReceipts = ExVAT − ExpectedRefunds − PaymentFees
Royalty = DefinedNetReceipts × RoyaltyShare
ContributionBeforeAcquisition = DefinedNetReceipts − Royalty
                               − DeliverySupport − ExpectedDisputeCost
                             = 3.400275
ContributionAfterAcquisition = 1.900275

RecoveryBeforeAcquisition = ceil(1,500 / 3.400275) = 442 gross orders
RecoveryAfterAcquisition  = ceil(1,500 / 1.900275) = 790 gross orders
TitleOutcome(n) = n × 1.900275 − 1,500
CompanyCoverageOrders = ceil((SharedOverhead + NewTitleInvestment) / Contribution)
```

Cohort alternative, acquisition per reader rather than per order:

```text
ExpectedOrdersPerAcquiredReader = 1 + 0.45 + 0.25 = 1.70
AcquisitionPerNewReader = 5.00
RetentionCostPerAdditionalOrder = 0.20
CohortContribution = 1.70 × 3.400275 − 5.00 − 0.70 × 0.20 = 0.640 per reader
```

Collection: apply the same refund, payment, and royalty assumptions to €19.99 with €0.45 total delivery and dispute cost. Contribution is €8.87 per bundle order before acquisition, production, and overhead.

### A.3 Budget and advances

```text
Discretionary90DayBudget = 25,000
SharedMonthlyBudget = 8,000
Combined90DayAllocation = 25,000 + 3 × 8,000 = 49,000
IllustrativeOpeningCapital = 120,000
UncommittedAfterAllocation = 120,000 − 49,000 = 71,000
```

For a non-returnable advance recoupable against the same royalty pool, cumulative rights cash paid ordinarily reflects the larger of the advance and cumulative earned royalties. Track cash timing and unrecouped balances separately.

---

<a id="sources"></a>
## Appendix B. Source register

Research basis: 22 September 2026. Reference IDs keep their numbering from the original research record; unused IDs are omitted. Descriptions such as "page inspected" refer to that record, not to a re-check on the plan date. Statutes, judgments, official guidance, and vendor policies carry different authority. Contact pages identify public routes, not warm introductions or licensable inventory.

**Gaps in this version.** No source measures the English digital manga market. Established English manga publishers and official simulpub apps are not in the record. US consumer and sales-tax rules and UK VAT are not in the record. Japanese title, contract, and moral-rights practice is covered only by the Berne summary and the non-binding Japan Copyright Office AI explanation.

### Market and direct-sale mechanisms

- **R04** J-Novel Club — FAQ. Samples, memberships, premium files, series licensing, download policy. https://j-novel.club/faq
- **R48** J-Novel Club — How it works. Free samples, individual purchases, memberships; most manga at 899 coins, 100 coins = US$1. Not a willingness-to-pay study. https://j-novel.club/howitworks
- **R50** emaqi — Google Play developer listing, updated 11 September 2026. Licensed manga subscription in the US and Canada. Developer claims. https://play.google.com/store/apps/details?hl=en&id=com.emaqi.android
- **R69** Orange — official company site. Pages did not supply readable product text; production scope not reconfirmed. https://orange.inc/

### Competitors, platforms, and production

- **R45** Mantra — products and services. Manga translation, typesetting, editing, human-assisted services. https://mantra.co.jp/en/
- **R46** GlobalComix — FAQ on its acquisition of INKR, 19 March 2026. Opt-in localization, rights-holder control, human translators and letterers. https://globalcomix.com/forums/threads/13401/faq-regarding-globalcomix-s-acquisition-of-inkr
- **R47** WEBTOON CANVAS — translation-program notice, 26 March 2026. https://m.webtoons.com/en/notice/detail?noticeNo=3620
- **R49** viviON Translators Unite — translator guide and FAQ. Authorized translation, review, sales-linked rewards; rejects machine translation; restricts external sales. https://min-hon.net/translator/en/
- **R68** Comic Translate — repository README. Detection, OCR, inpainting, translation, rendering. Check component licenses before reuse. https://github.com/ogkalu2/comic-translate
- **R70** Amimaru — services and sales contact. https://amimaru.com/
- **R71** J-Novel Club — contact page. https://j-novel.club/contact
- **R74** TOKYOPOP — contact page. https://tokyopop.com/pages/contact-us

### Technical research and evaluation

- **R40** MQM Council — Translation Quality Metrics framework. Error categories and severity; the manga protocol still needs definition. https://www.themqm.org/
- **R42** Context-Informed Machine Translation of Manga using Multimodal LLMs, COLING 2025. Visual context, unit size, context length. Benchmark access is not commercial rights. https://arxiv.org/abs/2411.02589
- **R43** The Manga Whisperer, CVPR 2024. Panel, text, and character detection; reading order; speaker association. Check code, weight, and dataset licenses. https://arxiv.org/abs/2401.10224
- **R44** OnomatoBridge, preprint submitted 18 September 2026. Sound-effect translation and rendering. Not a launch capability. https://arxiv.org/abs/2609.21199

### Copyright, licensing, and authorship

- **R10** WIPO — Summary of the Berne Convention. Translation, adaptation, reproduction, moral rights. https://www.wipo.int/en/web/treaties/ip/berne/summary_berne
- **R11** Business.gov.nl — Copyright. Licensing, written exclusivity, creator-contract protections. https://business.gov.nl/regulations/copyright/
- **R12** Dutch Copyright Federation — Bewerken, vertalen, verfilmen. Adaptation rights versus underlying rights. https://www.auteursrecht.nl/Ik-wil-jouw-werk-gebruiken/Bewerken-vertalen-verfilmen
- **R13** Dutch Copyright Federation — Persoonlijkheidsrechten. Attribution and integrity rights; limits on waiver. https://www.auteursrecht.nl/Auteursrecht/Persoonlijkheidsrechten
- **R14** US Copyright Office — Title 17, Chapter 1. Sections 101, 103, 106, 107. US territorial analysis only. https://www.copyright.gov/title17/92chap1.html
- **R41** Dutch Copyright Federation — Works made with artificial intelligence. Human creative choices; not a court decision. https://www.auteursrecht.nl/Auteursrechtwijzer/Werken-gemaakt-met-kunstmatige-intelligentie
- **R51** Netherlands Auteurswet — WIPO Lex consolidation through 1 January 2026, Dutch text. Translations, private copying, moral rights, technological measures. https://www.wipo.int/wipolex/en/legislation/details/23781
- **R55** EU Directive 2019/790. Articles 3–4 text and data mining; not a license to publish translated entertainment. https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32019L0790
- **R56** US Copyright Office — AI and copyright, Part 2: Copyrightability, January 2025. Human authorship; prompts alone insufficient. https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf
- **R57** Japan Copyright Office — General Understanding on AI and Copyright, May 2024. Non-binding; distinguishes analysis from generation and exploitation. https://www.bunka.go.jp/english/policy/copyright/pdf/94055801_01.pdf
- **R67** CJEU, Tom Kabinet, C-263/18, 19 December 2019. Permanent-download ebook supply is communication to the public; not a translation case. https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:62018CJ0263

### Commerce, tax, consumer, privacy, accessibility

- **R20** Börsenverein — Buchpreisbindung. German fixed-price scope including ebooks; foreign-language and cross-border cases need counsel. https://www.boersenverein.de/beratung-service/recht/buchpreisbindung/
- **R21** Business.gov.nl — Setting fixed book prices. Ebooks excluded from the Dutch requirement. https://business.gov.nl/regulations/setting-fixed-book-price/
- **R23** Germany — Umsatzsteuergesetz §12. 7% for qualifying electronic publications. https://www.gesetze-im-internet.de/ustg_1980/__12.html
- **R24** European Commission — VAT One Stop Shop. Destination taxation; conditional €10,000 threshold. https://vat-one-stop-shop.ec.europa.eu/one-stop-shop_en
- **R25** Business.gov.nl — Rules for online sales and purchases. https://business.gov.nl/regulations/long-distance-sales-and-purchases/
- **R26** Business.gov.nl — Cancellation period in case of a sale; 19 June 2026 amendment notice. https://business.gov.nl/regulations/cancellation-period-sale/
- **R27** European Commission — Digital contract rules. Remedies for faulty digital content. https://commission.europa.eu/topics/business-and-industry/contract-rules/digital-contracts/digital-contract-rules_en
- **R28** Your Europe — Accessibility requirements. Ebooks and ecommerce from 28 June 2025; exemptions need assessment. https://europa.eu/youreurope/business/selling-in-eu/selling-goods-services/accessibility/index_en.htm
- **R31** European Commission — Transparency obligations under Article 50 of the AI Act, updated 24 July 2026. https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act
- **R33** Business.gov.nl — Protection of personal data (GDPR). https://business.gov.nl/regulations/protection-personal-data/
- **R34** Business.gov.nl — Cookies on your website. https://business.gov.nl/regulations/cookies/
- **R58** Your Europe — B2C ecommerce and distance selling. Precontract information; consent conditions for loss of withdrawal. https://europa.eu/youreurope/business/selling-in-eu/selling-goods-services/ecommerce-distance-selling/index_en.htm
- **R59** Belastingdienst — services subject to 9% VAT. Qualifying electronic publications; Dutch consumer case only. https://www.belastingdienst.nl/wps/wcm/connect/bldcontentnl/belastingdienst/zakelijk/btw/tarieven_en_vrijstellingen/diensten_9_btw/
- **R60** Your Europe — VAT One Stop Shop. https://europa.eu/youreurope/business/finance-and-tax/vat/one-stop-shop/index_en.htm
- **R61** Stripe Netherlands — pricing. Standard EEA cards 1.5% + €0.25; the 2.5% + €0.25 planning rate is a blended assumption. https://stripe.com/nl/pricing
- **R62** Your Europe — GDPR compliance. https://europa.eu/youreurope/business/governance-and-sustainability/digital-and-data-compliance/data-protection-gdpr/index_en.htm
- **R63** European Commission — AI transparency guidelines, updated 6 August 2026. https://digital-strategy.ec.europa.eu/en/policies/guidelines-ai-transparency-obligations

---

**End of proposal.**

[R04]: #sources "J-Novel Club — FAQ"
[R10]: #sources "WIPO — Summary of the Berne Convention"
[R11]: #sources "Business.gov.nl — Copyright"
[R12]: #sources "Dutch Copyright Federation — Bewerken, vertalen, verfilmen"
[R13]: #sources "Dutch Copyright Federation — Persoonlijkheidsrechten"
[R14]: #sources "US Copyright Office — Title 17, Chapter 1"
[R20]: #sources "Börsenverein — Buchpreisbindung"
[R21]: #sources "Business.gov.nl — Setting fixed book prices"
[R23]: #sources "Germany — Umsatzsteuergesetz §12"
[R24]: #sources "European Commission — VAT One Stop Shop"
[R25]: #sources "Business.gov.nl — Rules for online sales and purchases"
[R26]: #sources "Business.gov.nl — Cancellation period in case of a sale"
[R27]: #sources "European Commission — Digital contract rules"
[R28]: #sources "Your Europe — Accessibility requirements"
[R31]: #sources "European Commission — Article 50 transparency obligations"
[R33]: #sources "Business.gov.nl — GDPR"
[R34]: #sources "Business.gov.nl — Cookies"
[R40]: #sources "MQM Council — Translation Quality Metrics framework"
[R41]: #sources "Dutch Copyright Federation — Works made with AI"
[R42]: #sources "Context-Informed Machine Translation of Manga"
[R43]: #sources "The Manga Whisperer"
[R44]: #sources "OnomatoBridge"
[R45]: #sources "Mantra — products and services"
[R46]: #sources "GlobalComix — INKR FAQ"
[R47]: #sources "WEBTOON CANVAS translation-program notice"
[R48]: #sources "J-Novel Club — How it works"
[R49]: #sources "viviON Translators Unite"
[R50]: #sources "emaqi — Google Play listing"
[R51]: #sources "Netherlands Auteurswet"
[R55]: #sources "EU Directive 2019/790"
[R56]: #sources "US Copyright Office — AI and copyright, Part 2"
[R57]: #sources "Japan Copyright Office — AI and Copyright overview"
[R58]: #sources "Your Europe — B2C ecommerce"
[R59]: #sources "Belastingdienst — 9% VAT"
[R60]: #sources "Your Europe — VAT One Stop Shop"
[R61]: #sources "Stripe Netherlands — pricing"
[R62]: #sources "Your Europe — GDPR compliance"
[R63]: #sources "European Commission — AI transparency guidelines"
[R67]: #sources "CJEU, Tom Kabinet, C-263/18"
[R68]: #sources "Comic Translate repository"
[R69]: #sources "Orange — official company site"
[R70]: #sources "Amimaru"
[R71]: #sources "J-Novel Club — contact page"
[R74]: #sources "TOKYOPOP — contact page"
