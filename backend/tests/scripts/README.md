# Operator-Script Tests

Unit tests for `backend.scripts.*` operator helpers — verifies parsing, assertion, and exit-code logic without hitting real services.

## Files

| File | Surface under test |
|------|--------------------|
| `test_verify_langfuse_trace.py` | `backend.scripts.validation.verify_langfuse_trace` — D29 reasoning schema checks + abort-path contract (`reasoning_tail_aborted` key always required, `status="aborted"` on root chain) |

The verifier itself talks to Langfuse over the network; tests mock the SDK client and feed synthetic `LangfuseSpan` / `LangfuseGeneration` objects to exercise the assertion paths.

## Run

```bash
uv run pytest backend/tests/scripts/ -q
```

## Operator-helper docs

The CLI synopsis, flag table, per-mode assertions, env vars, and exit codes for each operator helper live in the per-script README — e.g., `backend/scripts/validation/README.md` for `verify_langfuse_trace.py`. Tests here pin the assertion logic; the README explains when an operator should run the script and what passes / fails mean.

## Conventions

- One test file per operator script. Mirror the script's path under `backend/scripts/` (so `backend/scripts/validation/verify_langfuse_trace.py` → `backend/tests/scripts/test_verify_langfuse_trace.py`).
- For network egress paths, mock at the SDK client boundary (`langfuse.get_client`, etc.) so tests stay deterministic and offline.
- Cover both success and explicit failure modes (e.g., missing key, wrong value type) so a future operator gets a precise CLI error message instead of a stack trace.
