# RAG Ablation — Answer Quality (whole-section reading vs RAG bundle)

> **One-line takeaway:** On the 2026-10-22 RAG bundle ablation's own answers, none of the
> three quality lenses shows a loss from the RAG bundle. Signal pass rate Δ (B − A)
> −0.007 [−0.044, +0.033] over 90 paired answers; faithfulness support rate 0.990 vs 0.993, Δ +0.003 [−0.010, +0.014], with 3 contradicted claims in each arm; vital key-point recall
> Δ −0.009 [−0.035, +0.014]. The ablation's efficiency gains (−34k SEC tokens, −12.4 s,
> −69% cost) therefore come without a measurable quality cost **at this sample size**.

This archive adds the quality measurement that the
[2026-10-22 RAG bundle ablation](../2026-10-22-rag-bundle-ablation/report.md) left pending
(its §6 blind review was never run). It re-uses the judges, prompts and blinding of the
[reader model × reasoning benchmark](../2026-10-28-reader-model-reasoning/report.md)
(§4.1 and §5). No new agent runs: every answer and tool output graded here is from the
ablation's `raw.tar.gz`. The ablation archive itself is unchanged.

## 1. Arms

| | Arm A `luna_medium` | Arm B `reader_luna_medium` |
|---|---|---|
| Model | GPT-5.6 Luna, effort `medium` | same |
| 10-K access | `sec_filing_list_sections` + `sec_filing_get_section` (whole sections) | same + `sec_filing_search` (chunk search) |
| Prompt | baseline benchmark prompt | reader prompt (grounding + `[N]` citation rules) |

This measures the **bundle** (tool + reader prompt), as the ablation did. Paired Δ is
B − A per row; 95% CIs are row-level bootstrap (30 rows).

## 2. Results

| Lens | Scope | Arm A (whole sections) | Arm B (RAG bundle) | Δ B − A [95% CI] |
|---|---|---|---|---|
| Signal pass rate | 3 reps, 90 answers/arm | 0.959 [0.919, 0.989] | 0.952 [0.915, 0.981] | **−0.007 [−0.044, +0.033]** |
| Signal pass rate | rep 1, 30 answers/arm | 0.956 [0.911, 0.989] | 0.967 [0.933, 1.000] | +0.011 [−0.022, +0.056] |
| All 3 signals pass | 3 reps | 0.878 [0.756, 0.967] | 0.878 [0.789, 0.956] | +0.000 [−0.089, +0.100] |
| Faithfulness: claims checked | rep 1, 30/arm | 621 | 537 | — |
| Faithfulness: support rate | rep 1, 30/arm | 0.990 [0.984, 0.996] | 0.993 [0.983, 1.000] | **+0.003 [−0.010, +0.014]** |
| Faithfulness: unsupported / contradicted claims | rep 1 | 4 / 3 | 1 / 3 | — |
| Faithfulness: answers with ≥ 1 contradicted claim | rep 1 | 3 / 30 | 1 / 30 | — |
| Vital key-point recall | rep 1, 30/arm | 0.988 [0.975, 1.000] | 0.978 [0.956, 0.996] | **−0.009 [−0.035, +0.014]** |
| All key-point recall | rep 1, 30/arm | 0.931 [0.893, 0.965] | 0.898 [0.866, 0.928] | −0.033 [−0.081, +0.019] |
| Vital recall, benchmark's checklist (sensitivity) | rep 1, 30/arm | 0.902 [0.854, 0.946] | 0.932 [0.903, 0.959] | +0.030 [−0.028, +0.091] |

### Judge validity (known-worse controls in the same blinded pools)

| Check | Result | Benchmark (same judge) |
|---|---|---|
| Signal: `off_topic` (another row's answer) | rate 0.00, Δ −0.96 | 0.00 — PASS |
| Signal: `truncated` (first ~15%) | rate 0.62, Δ −0.34 [−0.44, −0.24] | PASS (Δ ≤ −0.25) |
| Signal: `evidence_stripped` | rate 0.77, Δ −0.20 [−0.29, −0.11] | **misses the −0.25 bar**, same as the benchmark's Luna-only pool (−0.21) |
| Faithfulness: one figure altered +40% | flagged 11 of 12; the miss was a citation label ("Section 7" → "Section 10"), not a claim, so 11/11 valid alterations caught | 26/28 |
| Completeness: `truncated` | vital recall 0.56, Δ −0.43 [−0.48, −0.38] | −0.42 — PASS |

The signal judge is coarse on Luna answers, as in the benchmark: 79 of 90 (row, signal)
pairs were passed by every real answer in both arms. It catches gross failures, not
fine differences. The faithfulness and completeness lenses carry the finer signal.

## 3. What the numbers say

1. **Signals: no difference.** 23 of 30 rows tie on mean pass rate across reps; B is
   lower on 4 rows and higher on 3. B's single biggest loss is one **empty answer**
   (row 21, rep 3): the run finished normally with health 1.0 and six tool calls but
   returned no text, so it fails all three signals. A had no empty answer. Most other
   failures in both arms are the same "state the caveat / limits" signal (rows 24, 26).
2. **Faithfulness: no difference in support.** Both arms support ~99% of their
   checkable claims from their own evidence. Arm A states more claims (621 vs 537)
   because it read more text. Contradictions are rare in both: 3 claims each. A's 3 sit
   in 3 different answers, while B's 3 all come from one answer (row 22, below). With
   n = 30, "3 vs 1 answers" says nothing about which arm is better. The **kind** of error
   differs, though: A's are synthesis slips over long text (an inverted comparison, a
   unit error, a misread direction), and B's is picking the wrong year column from a
   retrieved financial table.
3. **Completeness: no loss at the vital level.** Both arms cover almost all vital key
   points (0.99 vs 0.98). On *all* key points B trails by 0.03, CI crossing 0, which
   is in the direction one would expect if whole sections surface more side detail.
   The direction flips (+0.03) with the benchmark's checklist, which was drawn from
   RAG-reader answers only. Both are within noise; the checklist choice matters about
   as much as the arm.

## 4. Examples

**B, RAG bundle — wrong column from a retrieved table (row 22, Alphabet free cash flow).**
The answer gave Google's capex as "約 323 億美元" and derived free cash flow "約 1,325 億美元".
The retrieved cash-flow table lists purchases of property and equipment as
(32,251) / (52,535) / (91,447) for 2023 / 2024 / 2025. The answer took the 2023 column,
so FY2025 FCF is overstated by about $59B (≈ $73B, not $132.5B). The same answer also
wrote the $10.0B revolving credit facility as 10 億 (= $1B). This is B's only answer
with contradictions.

**A, whole sections — inverted comparison (row 5).** The answer said cash and short-term
investments (374.16 億) are "higher than" total debt (465.85 億). Its own figures show
the opposite. The evidence was there; the synthesis flipped it.

**A, whole sections — unit error (row 17).** Sales and marketing expense of $47,129M
was written as "47.129 億美元" (≈ $4.7B), ten times too small (should be 471.29 億).

## 5. Method (deltas from the benchmark)

Same prompts (signal judge prompt sha256 `b38f46293a91`, identical to the benchmark's),
same row-bootstrap code, fresh context-free Claude Code subagent per batch (model
`claude-opus-5-5`; produced none of the answers), items pooled with controls, shuffled
with a fixed seed, given opaque ids, `sec://` ids masked. Keys are in the
`KEY_do_not_share/` directories, never shown to a judge. Differences:

- **Signal judge:** all 90 answers per arm (3 reps) + 90 controls = 270 items, 9
  batches. No within-pool re-judge (time).
- **Faithfulness:** rep 1, 60 real answers + 12 perturbed (6 per base arm). Arm A's
  evidence is whole 10-K sections: median 139k characters per run, max 1.1M, far
  beyond what a judge can read in one pass. So each item's evidence was written to its
  own file, batches were 3 items (benchmark: 6), and the judge got an addendum
  ([`faith_addendum.md`](grounding/faith/faith_addendum.md)) telling it to search the
  evidence for each claim before labelling it unsupported. Both arms got the same
  procedure. Evidence files are in `grounding/faith/evidence.tar.gz`.
- **Completeness:** the benchmark's per-row checklists fit the same 30 questions, but
  they were written from four RAG-reader arms' answers only, which would tilt toward
  arm B. The primary checklist was therefore rebuilt the benchmark's way from **both
  arms'** rep-1 answers (6 batches, anonymised and shuffled). The benchmark's checklist
  was scored too, as a sensitivity check.
- **Blinding limit.** Arm identity is partly visible from the answers (B uses `[N]`
  citations under the reader prompt) and, for faithfulness, from the evidence (whole
  sections vs search chunks). Judges were not told which system produced what, but a
  judge could infer the retrieval style.

## 6. Claim boundary

- **Rep 1 only** for faithfulness and completeness (30 answers per arm); signals use
  all 3 reps. With n = 30, a difference smaller than ~0.03–0.05 on these scales is not
  detectable.
- **LLM judges, no human check.** The benchmark's human spot-check is still pending;
  the checklists were not reviewed by a human.
- **Faithfulness is against the run's own evidence**, not the world. A claim the
  evidence lacks is "unsupported" even if true. Arm A sees more raw text, so it has
  more chances to be supported and more to contradict.
- **Bundle, not tool.** Prompt and tool changed together, as in the ablation.

## Files

| Path | What |
|---|---|
| `summary.json` | All numbers above |
| `judge/` | Signal judge prompt, 9 batches, results, `judge_scores.json`; key in `judge/KEY_do_not_share/` |
| `grounding/faith/` | Faithfulness prompt + addendum, 24 batches, results, `evidence.tar.gz`; `grounding/faith_scores.json` |
| `grounding/nuggets/` | Fresh checklists (prompt, batches, results) |
| `grounding/coverage/`, `grounding/coverage_prior_checklist/` | Coverage batches/results against the fresh and the benchmark's checklist |
| `grounding/KEY_do_not_share/` | Faithfulness and coverage keys |
| `scripts/` | `build.py`, `build_cov.py`, `score.py` (run with `PYTHONPATH=<repo>`; inputs: the ablation's extracted `raw/`) |

## Reproduce

```bash
mkdir -p /tmp/abl && tar -xzf ../2026-10-22-rag-bundle-ablation/raw.tar.gz -C /tmp/abl
```

```bash
PYTHONPATH=$PWD uv run python data/experiment-archives/2026-10-28-rag-ablation-quality/scripts/build.py /tmp/abl/raw data/experiment-archives/2026-10-28-rag-ablation-quality
```

Then one fresh subagent per batch (prompt + batch file only), `build_cov.py` after the
checklists, and `score.py <archive> data/experiment-archives/2026-10-28-reader-model-reasoning/grounding/nuggets`.
The ablation archive lives on `feat/rag-bundle-ablation` (commit `d305186`).
