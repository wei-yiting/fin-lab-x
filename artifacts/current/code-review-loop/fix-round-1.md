# Fix Round 1

> Fixer: claude-opus (subagent) | Date: 2026-07-21
> Commit: `5db529e14e6c16885188e76b6bcd941df001d0b7` (docs-only, not pushed until confirmation round)

### Fixed

| Issue ID | How Fixed | Files Changed |
|----------|-----------|---------------|
| M-1.1 | Rewrote the **Commit marker** definition to match the actual two-write state machine: marker point written `status: "pending"` at ingest start (vectorizer.py:113-126), overwritten `status: "complete"` as the final commit step (vectorizer.py:229-242); retrieval treats only a `complete` marker as present (`check_commit_marker_complete`, common.py:39-42); write-`complete`-last discipline is what makes "committed or absent" hold. | `CONTEXT.md` |
| SP-1.1 | Reworded the `_Avoid_` note to reflect delivered reality — code identifiers already renamed to `commit_marker_*`, term survives only in `backend/ingestion/sec_dense_pipeline/README.md` prose. Verified by `grep -rn -i sentinel backend/ingestion/`: the four remaining hits are all in that README (lines 24, 44, 78, 80); no `sentinel` identifiers remain in code. | `CONTEXT.md` |
| M-1.2 | Removed the inline zone enumeration; the entry now defines the concept and points to design-envelope §4 as the authoritative list (used the user-approved wording, un-wrapped to one line to match the file's per-sentence style). | `CONTEXT.md` |

### Not Fixed (with reason)

| Issue ID | Reason |
|----------|--------|
| — | All three issues fixed. |

### Reverted (fix broke tests)

| Issue ID | What Broke | Reverted Files | Suggested Alternative |
|----------|------------|----------------|----------------------|
| — | | | |

### Tests Run

| Test Command | Result | Notes |
|--------------|--------|-------|
| `git diff --stat` | ✅ Pass | Only `CONTEXT.md` changed (3 insertions, 3 deletions). |
| `grep -rn -i sentinel backend/ingestion/` | ✅ Pass | 4 hits, all in `sec_dense_pipeline/README.md` — confirms the `_Avoid_` note's claim. |

No pytest run: docs-only diff.

### Tests Added or Modified

| Test File | Added/Modified | What It Tests |
|-----------|----------------|---------------|
| — | | |

### Rewritten entries (verbatim)

Commit marker entry:

```markdown
**Commit marker**:
A per-(ticker, year) point written as `status: "pending"` at ingest start, then overwritten as `status: "complete"` as the final commit step. Retrieval treats only a `complete` marker as present; the write-`complete`-last discipline is what makes "committed or absent" hold.
_Avoid_: sentinel point (legacy term; code identifiers already renamed to commit_marker_* — the term survives only in backend/ingestion/sec_dense_pipeline/README.md prose, to be updated when that doc is next touched)
```

Production-Grade Zone entry:

```markdown
**Production-Grade Zone**:
An area held to full production standard because it is the portfolio value itself. The authoritative zone list and per-zone standards live in design-envelope §4 — never enumerate them elsewhere.
```
