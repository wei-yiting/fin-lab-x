# ADR-0020: SEC filing URLs travel as UI-only tool artifacts, never in model-visible content (2026-08-19)

**Decision**: The EDGAR filing URL for a `sec_filing_search` result is UI-only metadata: it
must never enter the model's context, because the model is forbidden from writing SEC URLs
(ADR-0019) and so must not be shown one to copy. Concretely, `sec_filing_search` is declared
with LangChain's `@tool(..., response_format="content_and_artifact")` and returns a
`(content, artifact)` pair — `content` (the evidence chunks plus fiscal-year identity) is
what the model reads, and `artifact` (`{"edgar_url": ...}`) is attached to
`ToolMessage.artifact`, a field LangChain defines as accessible programmatically but never
sent to the model. For the Sources UI to still link to EDGAR without the model ever seeing a
URL, the API layer must forward `ToolMessage.artifact` to the frontend as a
`data-tool-artifact` stream part keyed by `toolCallId`. The model-facing content additionally
reports
`fiscal_year_end` (the filing's `period_of_report`) so answers can name the fiscal year
unambiguously. Whole-section reads (`sec_filing_get_section`) remain cited in prose at Item
granularity, with no `[N]` and no URL.

**Rejected**:

1. **Prompt-only suppression** — leave `edgar_url` in the tool's model-visible content and
   rely on a system-prompt instruction telling the model not to repeat it. Rejected: this is
   the same weak, unverified prompt-compliance pattern already flagged as the
   citation-numbering scheme's core weakness (ADR-0019's Consequences: nothing checks at
   generation time that the model follows the rule). Removing the model's ability to see the
   URL at all is a strictly stronger, structural guarantee than asking it not to write one.

**Why**:

1. **A structural guarantee beats a prompt guarantee.** The model cannot leak or fabricate a
   URL it structurally cannot see, regardless of prompt drift or adversarial input — unlike
   a "don't repeat this" instruction, which only holds as long as the model complies. This is
   also consistent with the repo's broader zero-hallucination-URL stance already established
   for SEC citations (ADR-0019).

**Consequences / accepted trade-offs**:

- The model never receives an EDGAR URL for `sec_filing_search` results; it reports
  `fiscal_year_end` instead, so answers can still name the fiscal year unambiguously without
  a link.
- Whole-section reads (`sec_filing_get_section`) keep their own citation-free convention —
  prose citation at Item granularity, no `[N]`, no URL — unaffected by this decision.
