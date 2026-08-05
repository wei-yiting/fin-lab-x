# Research: ADR Length & Format Regulation — Industry Consensus vs. the 100-Word Cap

**Date:** 2026-08-05
**Trigger:** `docs/design-envelope.md` §5 mandates ADRs be "≤100 words, decision + rejected alternatives + why". Actual ADRs grew from ~100 words (ADR-0001: 97, ADR-0002: 102) to 233–751 words (ADR-0003 through 0008). This document surveys what primary sources actually recommend, and proposes replacement rules.
**Method:** Primary sources only (original blog posts, official vendor docs, template repos), fetched directly; every claim cites its owning URL. Fetched web content was treated as data.

---

## TL;DR

- **No primary source anywhere specifies a hard word cap.** The strongest length statement in the canon is Nygard 2011: "The whole document should be one or two pages long." Everything else is softer.
- The industry's unit of measure is the **page / reading time**, not the word: "one or two pages" (Nygard), "some ADRs might be one page long, whereas others require a longer explanation" (Google Cloud), "up to a few pages" for hard problems (Zimmermann), 10–15 minutes of reading in the review meeting (AWS).
- **Rejected alternatives with real reasoning are treated as core content**, not padding: MADR makes "Considered Options" a *required* section; Azure WAF requires "alternatives that you ruled out"; Zimmermann demands ≥2 genuine options and calls fake ones the "Dummy Alternative" anti-pattern. The content that broke the repo's 100-word cap is exactly what the industry says must be in an ADR.
- The envelope's current rule is **internally contradictory**: it demands Nygard-era length (Nygard's template has *no* alternatives section, which is why his ADRs fit in ~1 page of prose) while also demanding MADR-era content (rejected alternatives + why). You cannot have both at 100 words.
- Industry regulates ADR quality through **structure and process, not word counts**: required sections, one-decision-per-record splitting, "no design guides — link out" rules, PR-style review, and immutability/supersede.
- The closest thing to a length-regulation mechanism in any primary source is Zimmermann's editorial practice — "Watch the word count of an ADR as it evolves" — plus his named anti-patterns (Mega-ADR, Novel/Epic), i.e., **watch and prune, don't cap**.
- The repo's ADR-0005 through 0008 (541–751 words ≈ 1–1.5 pages rendered) are **inside industry norms**, not outliers. ADR-0001/0002 are closer to Y-statement scale, which is also fine — tiering is expected (MADR ships four template variants for this reason).

---

## Q1 — What do primary sources say about ADR length?

### Michael Nygard, "Documenting Architecture Decisions" (2011) — the origin

Source: https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions

- Length: **"The whole document should be one or two pages long."** Also "short text file" and "bite sized pieces". This is the only near-quantitative length statement among the foundational sources — and one page of prose is roughly 400–500 words, not 100.
- Style: "full sentences organized into paragraphs", written "as if it is a conversation with a future developer". Bullets "acceptable only for visual style, not as an excuse for writing sentence fragments".
- **No hard word cap. No rejected-alternatives section at all** (see Q2) — which is why Nygard-style ADRs can be short.

### MADR project (adr.github.io/madr, github.com/adr/madr)

Sources: https://adr.github.io/madr/ ; https://github.com/adr/madr ; https://raw.githubusercontent.com/adr/madr/develop/template/adr-template.md ; https://raw.githubusercontent.com/adr/madr/develop/template/adr-template-minimal.md

- **No length guidance at all** beyond one micro-suggestion: the Context and Problem Statement should be "two to three sentences or in the form of an illustrative story".
- Length is regulated by **template tiering** instead: MADR 4.x ships four variants — full, minimal, bare, bare-minimal — and tells teams to "copy the template" and "adapt" per decision. Design goal: make it "as easy as possible to a) write down the decisions and b) to version the decisions".

### adr.github.io (main ADR organization site)

Source: https://adr.github.io/

- Defines ADR/AD/ASR/decision log. **No statements about length or brevity anywhere on the site.** Catalogs templates (Nygard, MADR, Y-statements) without ranking them.

### AWS Prescriptive Guidance, "Architectural decision records"

Sources: https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html ; https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/best-practices.html

- **No word or page cap.** Minimum content: "each ADR should define the context of the decision, the decision itself, and the consequences".
- Implicit length signal via the review process: the review meeting starts with "a dedicated time slot to read the ADR. On average, **10 to 15 minutes** should be enough" — a reading-time budget, which accommodates a 1–3 page document, not a 100-word one.
- Regulation is process-based: Proposed → review meeting → Accepted/Rejected; "When the team accepts an ADR, it becomes immutable"; changes require a new superseding ADR.

### Google Cloud, "Architecture decision records overview"

Source: https://docs.cloud.google.com/architecture/architecture-decision-records (301 from cloud.google.com/architecture/architecture-decision-records)

- Explicitly refuses a length rule: **"Some ADRs might be one page long, whereas others require a longer explanation."**
- Recommended content includes "Overview of the key options" and "Your decision and reasons behind the accepted choice" — i.e., options are core content.

### Microsoft Azure Well-Architected Framework, "Maintain an architecture decision record"

Source: https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record

- Closest any vendor doc comes to a brevity rule — and it is qualitative: **"Keep records pithy, assertive, on-topic, and factual."**
- The overflow valve is a link-out rule, not a cap: "Avoid making decision records design guides. If more justification or design ideation is available, provide a link to a document as supplemental material, but the decision must be clear and stand alone without that material."
- Requires documenting "alternatives that you ruled out", "important tradeoffs made with this decision", and even "the confidence level of the decision". Append-only: "Don't go back and edit accepted records."

### ThoughtWorks Technology Radar, "Lightweight Architecture Decision Records"

Source: https://www.thoughtworks.com/en-us/radar/techniques/lightweight-architecture-decision-records

- Rated **Adopt** (Nov 2017, May 2018; Trial in 2016–17): "For most projects, we see no reason why you wouldn't want to use this technique."
- "Lightweight" refers to **format and storage** (simple markup files "in source control", per adr-tools), not to a word count. **No length figure appears in the entry.** (Inference: "lightweight" is contrasted with heavyweight decision-documentation frameworks like Tyree/Akerman, not with 500-word text files.)

### GitHub Engineering blog, "Why Write ADRs"

Source: https://github.blog/engineering/architecture-optimization/why-write-adrs/

- Argues in the *opposite* direction from a cap: "ADRs force you to write **more** than a one-liner 'this ships the feature for #3128'." Names "Alternatives Considered" and "Pros/Cons" as sections GitHub uses. No length guidance.
- Process: write the ADR *before* the PR so it improves PR review.

### arc42, Section 9 (Architecture Decisions)

Source: https://docs.arc42.org/section-9/

- Recommends Nygard's five-part template verbatim. Brevity guidance is about **selection, not compression**: document "a few important decisions" ("important, expensive, large scale or risky"), and "Smaller pieces of documentation are easier to read, create and maintain". "Avoid redundant texts" — don't duplicate what's documented elsewhere. No word/page figure.

### Y-statements — Olaf Zimmermann

Sources: https://medium.com/olzzio/y-statements-10eb07b5a177 ; https://ozimmer.ch/practices/2023/04/03/ADRCreation.html ; https://ozimmer.ch/practices/2020/05/22/ADDefinitionOfDone.html

- The Y-statement is the one genuinely length-constrained format in the canon: "In the context of \<use case\>, facing \<concern\>, we decided for \<option\> and neglected \<alternatives\>, to achieve \<benefit\>, accepting that \<drawback\>." — "The six sections of the resulting AD records form one (rather long) sentence." Origin: a colleague "challenged me to fit each decision on one presentation slide (including rationale!)".
- But even here the constraint is elastic: "It is perfectly fine to modify the template; for instance, an extra half sentence starting with 'because' can supply additional justifications."
- Zimmermann's later, fuller guidance ("How to create ADRs — and how not to", 2023) is the most direct answer to the length question in any primary source: **"Sometimes, one presentation slide with few sentences is enough"** for simple decisions, but **"more wicked problems may require more elaborate decision rationale, up to a few pages"** — and the regulation mechanism is editorial: **"Watch the word count of an ADR as it evolves."** His named anti-patterns bound the upper end: *Mega-ADR* (detailed component specs/diagrams/code stuffed in — "move detailed design to separate documentation") and *Novel/Epic* (a whole architecture document squeezed into one ADR).

### Verdict on Q1

**Zero primary sources impose a hard word cap.** The distribution of actual guidance: one-slide/one-sentence (Y-statement) → "one or two pages" (Nygard) → "one page … or longer" (Google) → "up to a few pages" for wicked problems (Zimmermann) → "pithy" + link-out (Azure). A 100-word hard cap is stricter than every source surveyed, including the format explicitly designed to fit on a single slide. (Secondary sources — not authoritative, but confirming the norm — converge on "1–3 pages / ~400 words / readable in 5 minutes", e.g. https://embeddedartistry.com/fieldmanual-terms/architecture-decision-record/.)

---

## Q2 — Structural conventions and the brevity-vs-completeness tension

| Template | Sections | Rejected alternatives | How it resolves brevity vs completeness |
|---|---|---|---|
| **Nygard (2011)** | Title, Context, Status, Decision, Consequences | **Absent** — no options section; only the chosen path and its consequences | Short *because* incomplete on alternatives; prose discipline ("full sentences", "one or two pages") |
| **Y-statement (Zimmermann)** | One sentence: context / facing / we decided / and neglected / to achieve / accepting that | **Inline and mandatory** — "neglected alternatives not chosen (not to be forgotten!)" — but named only, not argued | Extreme compression; alternative *reasoning* is sacrificed, optionally restored via "because" clauses |
| **MADR full (4.x)** | Required: Context and Problem Statement, Considered Options, Decision Outcome. Optional (each marked "This is an optional element. Feel free to remove."): Decision Drivers, Consequences, Confirmation, **Pros and Cons of the Options**, More Information | Listing options **required**; per-option Good/Neutral/Bad argumentation **optional** | Tiering: four template variants; teams "adjust optional/required parts according to project/product context" (MADR primer) |
| **MADR minimal** | Context and Problem Statement, Considered Options, Decision Outcome, Consequences (Good/Bad bullets) | Options listed; no per-option rationale section | The default when a decision doesn't need argued trade-offs |
| **arc42 §9** | Nygard's five parts, or "list or table, ordered by importance" | Follows Nygard (absent) | Regulates by *selection* (document few decisions) and non-redundancy, not per-document length |
| **Azure WAF record** | Problem statement + context, Options considered, Decision outcome (with tradeoffs + confidence level), Status | **Required** ("including alternatives that you ruled out") | "Pithy" norm + link-out rule for design detail + split multi-phase decisions into multiple records |

Key structural findings:

1. **The essential core has converged on 3–5 elements.** Zimmermann's MADR primer (https://ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html): "Many sections are optional. We see **three to five elements as the essence of an ADR**" — title, context/problem, (drivers), considered options, decision outcome. He notes MADR-minimal is "quite close to Michael Nygard's ADR proposal from 2011" and "corresponds well with the parts of Y-Statement sentences" — the three lineages agree on the skeleton.
2. **Post-2011 templates all promoted alternatives into the record.** Nygard omitted them; every successor (Y-statement 2012, MADR, Azure, Google, GitHub's practice) includes them, and most make listing them mandatory. What stays *optional* is the depth of per-option argumentation (MADR's "Pros and Cons of the Options").
3. **Rationale is the one thing no template lets you drop.** Joel Parker Henderson's catalog (https://github.com/joelparkerhenderson/architecture-decision-record): "Explain the reasons for doing the particular AD… A rationale that is good today may not be good later." Azure: "A record without justification loses its value over time." AWS: the ADR "focuses on the reason for the decision rather than how the team implemented it… prevents other architects who weren't involved… to overrule that decision in the future."
4. **The years-later usefulness test favors the exact content our over-cap ADRs contain** — argued alternatives, accepted trade-offs, consequences. (Inference: a 100-word record that names alternatives without the "why not" fails the stated purpose of the AWS/Azure/JPH guidance.)

---

## Q3 — How teams regulate ADR quality in practice

Mechanisms actually found in primary sources, roughly ordered by prevalence:

1. **Required-section templates** (universal). AWS: "a team member starts to write the ADR based on a projectwide template. The template… ensures that the ADR captures all the relevant information." Zimmermann's ADR Author Pledge: "choose single template format consistently."
2. **Review gates** (AWS, GitHub). AWS runs a synchronous review meeting (10–15 min silent read, then comment walkthrough) with Proposed/Accepted/Rejected outcomes. GitHub writes the ADR *before* the PR so the PR review doubles as the ADR review. ThoughtWorks/adr-tools keep ADRs in source control, which makes PR review the natural gate.
3. **Immutability + supersede** (AWS, Azure, JPH, and this repo already). "Append-only log… Don't go back and edit accepted records" (Azure). This is a *quality* mechanism: it forces each record to be a self-contained point-in-time argument.
4. **One decision per record / split rule** (JPH: "Each ADR should be about one AD, not multiple ADs"; Azure: "Break one decision into multiple if an architectural decision is going to result in multiple phases"). This is the industry's actual answer to bloat — a long ADR is usually a fused ADR.
5. **Link-out rule for design detail** (Azure; Zimmermann's Mega-ADR anti-pattern: "Move detailed design to separate documentation"). Caps *scope*, not words: the record argues the decision; specs, diagrams, and code live elsewhere and are linked.
6. **Editorial word-count watching, anti-pattern vocabulary** (Zimmermann): "Watch the word count of an ADR as it evolves" + named smells (Mega-ADR, Novel/Epic, Blueprint/Policy Disguise, Dummy Alternative). A review vocabulary, not a numeric gate.
7. **Tiered formats** (MADR's four variants; Zimmermann's Definition of Done, https://ozimmer.ch/practices/2020/05/22/ADDefinitionOfDone.html, which requires documentation "preferably in a lean and light template such as a Y-statement or a MADR" — either tier satisfies the DoD).
8. **Significance filters** (Spotify, arc42): regulate *how many* ADRs, not how long. Spotify (https://engineering.atspotify.com/2020/04/when-should-i-write-an-architecture-decision-record): write one "whenever a decision of significant impact is made; it is up to each team to align on what defines a significant impact", and "ADRs can be lightweight."

**Hard word/length caps: effectively absent from practice.** No engineering-org write-up or official guide surveyed imposes one. The nearest real-world analogues are soft norms in secondary literature ("if your ADR exceeds one page, you're probably documenting multiple decisions or including implementation details" — which frames overflow as a *split/link* signal, not a compression signal).

---

## Q4 — Candidate replacement rules for envelope §5

All four candidates keep what §5 gets right (one file per decision, never edited, supersede by number, must contain decision + rejected alternatives + why) and replace only the "≤100 words" clause.

### Candidate A — One-page soft target with named escape hatch (recommended default)

> ADRs target **one page (~500 words)**. A record may exceed this only when the decision genuinely required argued trade-offs across ≥2 real options ("wicked problem"); reviewer judgment applies. Overflow is first treated as a **split or link-out signal**: multiple decisions → multiple ADRs; design detail → linked doc, decision must stand alone.

- **Supported by:** Nygard "one or two pages"; Google "some ADRs might be one page long, whereas others require a longer explanation"; Zimmermann "one slide… enough" / "up to a few pages" for wicked problems; Azure's link-out rule.
- **Trade-off:** soft targets need a reviewer who enforces them (in this repo, the PR gate already exists). Numbers in soft targets drift; the split/link-out test is what does the real work.
- **Fit check:** ADR-0005–0008 (541–751 words) would pass as-is or with light pruning; nothing needs rewriting.

### Candidate B — Cap only the Decision statement; structure the rest, no total cap

> Every ADR opens with a **one- or two-sentence Decision statement** (Nygard's "We will…" or a Y-statement). Below it, required sections with no overall cap: Context (2–3 sentences), Considered Options (each rejected option gets a one-line "why not"), Consequences (Good/Bad bullets). Per-option pros/cons argumentation is allowed but optional.

- **Supported by:** Nygard's Decision section style ("stated in full sentences, with active voice. 'We will…'"); MADR's required/optional split (Considered Options required, Pros and Cons optional); MADR's "two to three sentences" context guidance; Azure's required tradeoffs.
- **Trade-off:** regulates skimmability (the thing a cap actually protects) without capping substance; but a determined author can still bloat the optional sections — pair with Zimmermann's anti-pattern vocabulary for review.

### Candidate C — Y-statement TL;DR required at top + bounded body

> Every ADR begins with a single **Y-statement** ("In the context of…, facing…, we decided for… and neglected…, to achieve…, accepting that…"). The body below is free-form but bounded at ~one page, expanding only the "neglected" and "accepting that" clauses.

- **Supported by:** Zimmermann's Y-statement post (one-slide constraint, "neglected alternatives… not to be forgotten!"); his MADR primer showing Y-statement ↔ MADR-minimal correspondence; his DoD accepting either tier.
- **Trade-off:** best skim experience of the four (the decision log reads as a list of sentences — matches AWS's "skim the headlines" usage); costs some redundancy between TL;DR and body, and the six-clause sentence takes practice to write well.

### Candidate D — MADR-style two-tier template

> Default template = **MADR-minimal** (Context, Considered Options, Decision Outcome, Consequences — typically 100–250 words). Authors switch to the **full tier** (adds Decision Drivers + per-option Pros and Cons) when rejected alternatives need real argumentation. The trigger is content-based, never length-based; tier choice is visible in the PR diff.

- **Supported by:** MADR 4.x shipping full/minimal/bare/bare-minimal variants exactly for this; MADR primer: "one is free to revise the MADR template and adjust optional/required parts according to project/product context."
- **Trade-off:** most faithful to the strongest template lineage and legitimizes both the repo's short (0001/0002) and long (0005–0008) ADRs retroactively; but two tiers means a tier-choice judgment call per ADR, and the repo's current free-form ADRs would need restructuring into MADR headings.

### Cross-cutting recommendation (inference)

The 100-word cap failed because it capped the wrong variable: the industry caps **scope** (one decision, no design detail) and **skimmability** (decision statement up front), never **substance** (alternative reasoning). Any replacement should therefore combine: (1) a one-sentence decision statement or Y-statement at the top (B or C), (2) a one-page soft target with the split/link-out overflow test (A), and (3) Zimmermann's "watch the word count" + anti-pattern vocabulary as PR-review language rather than a numeric gate. Candidates A+B together are the smallest edit to envelope §5; D is the choice if the team wants to adopt an external standard wholesale.

---

## Source index

| Source | URL | Length stance |
|---|---|---|
| Nygard 2011 (origin) | https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions | "one or two pages" |
| adr.github.io | https://adr.github.io/ | none |
| MADR site | https://adr.github.io/madr/ | none (context: 2–3 sentences) |
| MADR repo + templates | https://github.com/adr/madr | tiered templates, no cap |
| AWS Prescriptive Guidance | https://docs.aws.amazon.com/prescriptive-guidance/latest/architectural-decision-records/adr-process.html (+ /best-practices.html) | 10–15 min read budget |
| Google Cloud | https://docs.cloud.google.com/architecture/architecture-decision-records | "one page… or longer" |
| Azure Well-Architected | https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record | "pithy" + link-out |
| ThoughtWorks Radar | https://www.thoughtworks.com/en-us/radar/techniques/lightweight-architecture-decision-records | "lightweight" (format), Adopt 2018 |
| GitHub Engineering | https://github.blog/engineering/architecture-optimization/why-write-adrs/ | "more than a one-liner" |
| arc42 §9 | https://docs.arc42.org/section-9/ | fewer decisions, smaller pieces |
| Y-statements (Zimmermann) | https://medium.com/olzzio/y-statements-10eb07b5a177 | one sentence / one slide |
| Zimmermann, ADR creation practices | https://ozimmer.ch/practices/2023/04/03/ADRCreation.html | "watch the word count"; slide → few pages |
| Zimmermann, MADR primer | https://ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html | 3–5 essential elements |
| Zimmermann, AD Definition of Done | https://ozimmer.ch/practices/2020/05/22/ADDefinitionOfDone.html | lean template (Y-statement or MADR) |
| Spotify Engineering | https://engineering.atspotify.com/2020/04/when-should-i-write-an-architecture-decision-record | "can be lightweight" |
| Joel Parker Henderson catalog | https://github.com/joelparkerhenderson/architecture-decision-record | no brevity rule; one decision per ADR |
