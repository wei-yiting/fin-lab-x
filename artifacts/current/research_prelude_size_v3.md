# Research — Prelude Size Re-validation under the Revised Detection Chain (v3)

> **Context**: DEV-127 R2 mandated re-running the prelude size probe with the new
> markdown H3/H4 detection before implementation. The first re-run (v2 probe,
> 2,000-cap design) surfaced failures that triggered a semantic re-analysis and a
> design revision (R2v2). This memo records both rounds. SSOT for the resulting
> decisions is DEV-127; design.md §5.2 mirrors them.

## Round 1 — v2 probe: original 24 probes, markdown detection + 2,000 cap

Script: `backend/scripts/research/prelude_size_probe_v2.py`
Sample: same 6 tickers × 4 items as the original ALL-CAPS-era research
(ADSK, JPM, JNJ, WMT, XOM, CAT × Items 1, 1A, 7, 7A).

Result: clean (<3,000 chars) preludes improved from 2/24 (8%, ALL-CAPS rule)
to 12/24 (50%) — 12/16 (75%) counting only items with a detected prelude.
But four disaster cases persisted:

| Case | Anchored headings | "Prelude" size | % of item |
|---|---|---|---|
| WMT 1A | 1 | 57,335 chars | 61% |
| WMT 1 | 2 | 16,116 chars | 43% |
| CAT 1 | 1 | 11,556 chars | 29% |
| JPM 1A | 12 | 6,402 chars | 6% |

And the two flagship TRUE preludes (CAT 7: 2,522; CAT 1A: 2,555) sat just
over the proposed 2,000 cap — the cap would truncate the design's own
founding examples.

## Semantic autopsy of the failures

Script: `backend/scripts/research/prelude_failcase_semantics.py`

The oversized "preludes" are not preludes. They are **detection failures**:

- **WMT 1A**: real block structure is four Title-Case standalone lines
  (`Strategic Risks` / `Operational Risks` / `Financial Risks` /
  `Legal, Tax, ... Risks`) that `filing.markdown()` marks at NO heading
  level. H3 anchored found 1 junk deep heading → "everything before it"
  swallowed 61% of the item's actual risk-factor content.
- **WMT 1 / CAT 1**: same disease — `General`, `Overview`,
  `Enterprise Strategy` etc. are real sub-headings markdown never marked.
- **JPM 1A**: mixed — genuine 2-paragraph prelude + swallowed content before
  the first anchored H4.

**Critical design implication**: prelude is excluded from chunking/embedding,
so a mis-classified pseudo-prelude means that text **disappears from the
vector index entirely** — a retrieval catastrophe, not a metadata-bloat
problem. A size cap on the attached metadata cannot fix this: the truncated
remainder still never gets chunked.

Root cause in the detection flow: "H3 anchored non-empty → use H3 path" is
too weak a condition. One junk anchored heading suppresses the text-fallback
path that would have found the real Title-Case headings.

## R2v2 — revised design (three-layer defense)

1. **Plausibility check** (fixes root cause): trust markdown H3/H4 anchored
   results only if anchored count ≥ 2 AND first anchored position ≤ 30% into
   the item text (thresholds tunable at implementation). Otherwise demote to
   the text-fallback path.
2. **Validity threshold** (semantic fuse, replaces "cap + truncate"): text
   before the first block heading is a valid prelude iff ≤ 3,000 chars —
   attached whole, never truncated. Larger ⇒ NOT a prelude ⇒ reclassified as
   a heading-less leading block, chunked + embedded normally, prelude
   metadata = None. **Zero content loss in every case.**
3. **No per-item gating** — the data does not support needing it.

## Round 2 — v3 probe: full revised chain, expanded sample

Script: `backend/scripts/research/prelude_probe_v3_full_algo.py`
Sample: 18 tickers × 4 items = 72 probes (original 6 + KO, BA, VZ, DIS +
NVDA, AAPL, MSFT, GE, PFE, GS, HD, COP). 63 analyzable non-stub items,
58 structured.

| Metric | Result |
|---|---|
| Valid prelude (≤3,000 chars) | **53/58 = 91.4%** (gate target was ≥70%) |
| Per-item valid rate | Item 1: 93.8% · 1A: 87.5% · 7: 87.5% · 7A: 100% |
| Path distribution | H3 25 · H4 25 · text fallback 8 · flat 5 |
| Plausibility demotions | 3 (fallback rescued 2; 1 → flat) |
| Reclassified leading blocks | 5 (JPM 1A, AAPL 1A, GE 7, PFE 1, GS 7) — all indexed, zero loss |
| Disaster cases from Round 1 | All fixed: WMT 1A → H4 path, true 812-char prelude; WMT 1 / CAT 1 → H4 path, 8/21 blocks, prelude 0; JPM 1A → reclassified |
| Flagship true preludes | CAT 7 / CAT 1A (~2.5k) attached whole |
| Valid-prelude size histogram | 0 chars: 17 · 1–500: 13 · 501–1,500: 20 · 1,501–3,000: 3 |

Notable: MSFT's four items all resolve via text fallback (markdown broken for
MSFT, consistent with `research_filing_markdown_quality.md`) and fallback
finds rich structure (27/14/41/5 blocks) — the fallback path is load-bearing,
not a corner case.

Flat cases (5): JNJ 7A (502 chars), CAT 7A (675), XOM 1 (6,640), VZ 7A
(6,993), GE 1A (61,747). GE 1A is the one large flat item — whole-item
chunking applies, no content loss, just no block structure.

## Verdict

The evidence gate passes decisively under R2v2: 91.4% ≫ 70%, zero
content-loss guarantee by construction, flagship cases preserved, and the
failure mode that motivated the gate (pseudo-prelude swallowing body text)
is structurally eliminated rather than merely capped.

Raw outputs (local, ephemeral): `/tmp/prelude_size_probe_v2_results.json`,
`/tmp/prelude_failcase_semantics.json`, `/tmp/prelude_probe_v3_results.json`.
Scripts are committed and re-runnable.
