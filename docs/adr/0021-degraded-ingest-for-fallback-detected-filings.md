# ADR-0018: Degraded ingest for fallback-detected filings (2026-08-21)

**Decision**: A filing whose filing-level section detection method (passed through from
upstream `Section.detection_method`) falls outside {`toc`, `heading`} is ingested
**degraded**: the section structure is not trusted, and the noise-cleaned full-document
markdown is stored as `ParsedFiling.degraded_text` with `items=[]`. The detection method is
recorded in `FilingMetadata.section_detection_method` for every parse (standard included).
Both fields are additive with defaults — a ratified change to the frozen `ParsedFiling`
schema (degraded-ingest spec, DEV-172) — so stored JSON from before the change still
validates. A structured parse that yields zero substantive items falls through to the same
degraded path: a trusted structure that produced nothing was not trustworthy.
`EmptyFilingError` therefore converges to a single meaning — even the degraded path's full
text came out empty after cleaning.

**Rejected**:

- **Mapping fallback section names back to Item keys** — the fallback name set is a closed
  upstream dictionary (8 names for 10-K) and, in the observed repro, detection found 1 of 8
  sections. Teaching the parser to recognize the shape does not repair the loss: most of the
  filing's content is still absent from the sections. The mapping has no consumer once the
  degraded path ingests the whole document.
- **Keeping only the partial mapped items** — ships a filing where most content is silently
  missing, indistinguishable from a good parse to every downstream consumer.
- **Partial items + full-text remainder hybrid** — the deduplication boundary between the
  mapped sections and the rest of the document is a permanent complexity tax on chunking,
  citation, and inspection, out of proportion to the marginal structure it preserves.
- **A self-built markdown Item splitter** — recovering structure with heading regexes over
  the markdown would be a fourth section detector, exactly the fragile hand-rolled work
  the rewrite onto edgartools' structured API (DEV-127) was adopted to escape.

**Why**: section detection is the upstream's competence and it degrades nondeterministically
(the AMD FY2025 repro parsed as `pattern`/1-section one day and `toc`/27-sections the next);
the parser's job on a degraded filing is to keep every word retrievable and the degradation
legible, not to reconstruct structure it cannot verify. Storing the cleaned full text makes
retrieval possible; the metadata marker makes "parse degraded, structure absent" permanently
distinguishable from source-level missing (DEV-171) and permanently observable via the
section-detection sweep (DEV-176).

**Noise cleaning is conservative by construction**: every rule is an opt-in cut anchored on
an observed render shape (cover page + INDEX before the first part heading, trailing
signature block, page-break artifacts); a document matching no anchor passes through
untouched. Leftover noise is acceptable; deleted content is not.

**Re-evaluate if**: edgartools v6.0 removes the legacy fallback detectors (rerun the
section-detection sweep (DEV-176) after any upgrade), or the A/B retrieval evaluation's
evidence (DEV-138) shows degraded chunks need retrieval scoring compensation (deferred
until evidence), or 10-Q support arrives with different degradation semantics.
