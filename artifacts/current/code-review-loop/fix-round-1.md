# Fix Round 1

> Fixer: Claude (code-fixer subagent) | Date: 2026-08-21

Issues dispatched after the Step 2.5 discussion gate. Both round-1 findings were
disputed at the gate and resolved by the user as **fix with modified direction**:

- **M-1.1** — user direction: fix only the CONTEXT.md wording (accurate parser-side
  description); dense-side chunking stays in its own slice (DEV-177), which now carries
  an acceptance criterion to restore the end-state wording once it lands.
- **m-1.1** — user direction: keep the DEV-* IDs for traceability but restructure every
  reference to description-first with the ID parenthesized ("the section-detection
  sweep (DEV-176)", never "the DEV-176 sweep").

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 | Replaced the overclaiming retrievability sentence in the "Degraded ingest" glossary entry with wording that describes only what the parser delivers today (full text preserved for later flat chunking) and states that retrieval arrives with the dense-side slice. Rest of the entry untouched. | `CONTEXT.md` |
| m-1.1 | Restructured all 7 DEV-* references to description-first with the ID parenthesized (IDs kept for traceability). DEV-171 reference verified already in the required shape; no change needed there. Rewrapped ADR lines 9–13 and 44–47 to keep the file's ~90-col wrapping. | `docs/adr/0018-degraded-ingest-for-fallback-detected-filings.md`, `backend/ingestion/sec_text_pipeline/README.md` |

### Not Fixed (with reason)

None — both issues fixed.

### Reverted (fix broke tests)

None.

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `uv run pytest backend/tests/ingestion/sec_text_pipeline/` | ✅ Pass | 195 passed |
| `uv run ruff format --check backend/` | ✅ Pass | 209 files already formatted |
| `uv run ruff check backend/` | ✅ Pass | All checks passed |

### Tests Added or Modified

None — both fixes are docs-only.

### Exact wording changes (before → after)

**CONTEXT.md, "Degraded ingest" entry (M-1.1):**
- Before: "All content stays retrievable, but without Item anchors."
- After: "The full text is thereby preserved for later unstructured flat chunking; retrieval of degraded filings (without Item anchors) arrives with the dense-side flat-chunking slice (DEV-177)."

**ADR-0018 (m-1.1):**
- DEV-172: "a ratified change to the frozen `ParsedFiling` schema (DEV-172)" → "a ratified change to the frozen `ParsedFiling` schema (degraded-ingest spec, DEV-172)"
- DEV-127: "exactly the fragile hand-rolled work DEV-127 adopted edgartools' structured API to escape." → "exactly the fragile hand-rolled work the rewrite onto edgartools' structured API (DEV-127) was adopted to escape."
- DEV-171: unchanged — already description-first.
- DEV-176 (first): "permanently observable (DEV-176 sweep)" → "permanently observable via the section-detection sweep (DEV-176)"
- DEV-176 (second): "rerun the DEV-176 sweep after any upgrade" → "rerun the section-detection sweep (DEV-176) after any upgrade"
- DEV-138: "the DEV-138 A/B evidence shows" → "the A/B retrieval evaluation's evidence (DEV-138) shows"

**README.md (m-1.1):**
- L20: "plus the DEV-172 ratified additive fields for degraded ingest (`degraded_text`, `section_detection_method` — defaults keep pre-change stored JSON readable)" → "plus the ratified degraded-ingest additive fields (DEV-172): `degraded_text` and `section_detection_method` — defaults keep pre-change stored JSON readable"
- L62: "(precedent: the DEV-172 degraded-ingest fields, additive with defaults)" → "(precedent: the degraded-ingest fields (DEV-172), additive with defaults)"

No dense pipeline code was touched; changes are confined to the three doc files.
