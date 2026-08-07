# common

Cross-subsystem domain types and helpers that more than one feature area depends on. Each module here is consumed by at least two callers (e.g. `agent_engine` + `ingestion`) and stays narrow on purpose.

## Modules

| Module | Companion doc | Summary |
|--------|---------------|---------|
| `sec_core.py` | [sec_core.md](../agent_engine/docs/sec_core.md) | Shared SEC filing layer: `FilingType`, `SECError` hierarchy, canonical 10-K item table, LRU-cached `fetch_filing_obj`, edgartools-error classification. |
| `errors.py` | — | Shared error taxonomy: `FinLabError` base plus the four cross-subsystem error classes (`TransientError`, `TickerNotFoundError`, `ConfigurationError`, `RateLimitError`) every subsystem must import rather than redefine. See [ADR-0012](../../docs/adr/0012-unified-error-taxonomy-under-finlaberror.md). |
| `retry.py` | — | `retry_transient` — the single tenacity-based retry decorator (`TransientError` only, 2 attempts total, exponential backoff + jitter, reraise). See [ADR-0013](../../docs/adr/0013-single-tenacity-retry-policy.md). |

## Conventions

- Import from submodules directly (`from backend.common.sec_core import FilingType`); `__init__.py` is intentionally empty so the import surface stays explicit.
- One module per domain. Don't bundle unrelated cross-cutting helpers into a single file — when a second domain shows up, it lives as a sibling module with its own companion doc, not a section in an existing one.
