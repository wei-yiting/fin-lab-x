# Validation Scripts

Operator helpers for post-deploy verification and on-demand diagnostics. All scripts are read-only — they fetch state, run assertions, and exit with a status code; none mutate the SEC cache, Qdrant index, or Langfuse traces.

## `validate_sec_md_cleanup.py`

Walks a `LocalFilingStore` cache directory, runs the cleanup-rule detectors (page separators, Part III stubs, heading variants, false-positive risks) against every cached 10-K markdown, and writes a report. Used to surface new boilerplate patterns or regressions before modifying `MarkdownCleaner`.

```bash
uv run python -m backend.scripts.validation.validate_sec_md_cleanup \
  --cache-dir data/sec_filings_html \
  --output artifacts/current/validation_cleanup_patterns.md
```

Both arguments are required. Output goes to `artifacts/` (gitignored).

When to run:

- Before or after changing a cleanup rule — diff baseline vs. updated report
- After downloading new tickers — check for unseen boilerplate variants
- When investigating a filing-specific regression

## `validate_sec_eval_dataset.py`

Validates the SEC retrieval eval dataset against a live Qdrant collection. Checks that `expected_header_paths` entries have matching chunks and reports near-miss warnings for case mismatches.

```bash
uv run python -m backend.scripts.validation.validate_sec_eval_dataset
uv run python -m backend.scripts.validation.validate_sec_eval_dataset --csv path/to/dataset.csv
```

| Argument | Required | Description |
|---|---|---|
| `--csv` | No | Path to dataset CSV (default: `backend/evals/scenarios/sec_retrieval/dataset.csv`) |

Collection and Qdrant URL are configured via environment variables `SEC_QDRANT_COLLECTION` and `QDRANT_URL`.

When to run:

- After changing chunking strategy, embedding model, or retrieval parameters
- When adding new ground-truth entries to the evaluation dataset
- As a smoke test after re-indexing the vector store

## `verify_langfuse_trace.py`

Polls Langfuse for a single trace and asserts the trace-level reasoning transcript shape (F7 / ADR-0016): the conversation's full reasoning lives in `metadata.reasoning` on the root `chat_turn` span, with `=== segment N ===` markers inside the value. Used by the BDD matrix and the abort scenario to confirm that a deployed change to the reasoning observability path still satisfies the trace-shape invariants.

```bash
uv run python -m backend.scripts.validation.verify_langfuse_trace <trace_id> --expect-reasoning-on
uv run python -m backend.scripts.validation.verify_langfuse_trace <trace_id> --expect-reasoning-on --expect-aborted
```

| Argument | Required | Description |
|---|---|---|
| `trace_id` | Yes | Langfuse trace id to fetch |
| `--expect-reasoning-on` | Yes | Assert the root-span `metadata.reasoning` transcript is non-empty and segment-marked |
| `--expect-aborted` | No | Also assert the root span carries `metadata.status == "aborted"` and that the transcript ends with the `=== aborted ===` marker (the scripted abort scenario cancels mid-segment) |

What it asserts:

- A root span (`parentObservationId is null`, type ≠ GENERATION) exists and carries `metadata.reasoning` (always-write-key contract).
- For `--expect-reasoning-on`: the transcript is non-empty, is not the `"<unsupported>"` sentinel, contains a `=== segment 1 ===` marker, and its segments carry non-whitespace text beyond the marker lines (a marker-only transcript fails).
- For `--expect-aborted`: root span has `metadata.status == "aborted"` and the transcript ends with the `=== aborted ===` marker.

The trace is fetched via the Langfuse Python SDK API client (`get_client().api.trace.get`). Authentication is via the standard Langfuse SDK env vars: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` (or the legacy `LANGFUSE_HOST`; default `https://cloud.langfuse.com`). The script polls 5× with linear backoff to absorb the ingestion lag between SSE close and the trace becoming queryable.

Exit codes:

- `0` — all assertions passed
- `1` — one or more assertions failed (errors printed in the JSON summary on stdout)
- `2` — could not reach Langfuse after all retry attempts (error printed on stderr)

When to run:

- After deploying a change touching the reasoning observability path (Langfuse callback, abort cleanup)
- When investigating a suspect trace surfaced by manual eval or user report
- As a one-shot verification step inside a BDD scenario script
