# common

Cross-subsystem domain types and helpers that more than one feature area depends on. Each module here is consumed by at least two callers (e.g. `agent_engine` + `ingestion`) and stays narrow on purpose.

## Modules

| Module | Companion doc | Summary |
|--------|---------------|---------|
| `sec_core.py` | [sec_core.md](../agent_engine/docs/sec_core.md) | Shared SEC filing layer: `FilingType`, `SECError` hierarchy, canonical 10-K item table, LRU-cached `fetch_filing_obj`, edgartools-error classification. |
| `config.py` | — | Repo-anchored data path resolvers (`get_duckdb_path`, `get_sec_filings_html_dir`, `get_sec_text_dir`, `get_checkpoint_db_path`) — anchored off this module's own file location so resolution is independent of the process's CWD, each overridable via its existing env var. See [ADR-0011](../../docs/adr/0011-repo-anchored-data-path-configuration.md). |

## Conventions

- Import from submodules directly (`from backend.common.sec_core import FilingType`); `__init__.py` is intentionally empty so the import surface stays explicit.
- One module per domain. Don't bundle unrelated cross-cutting helpers into a single file — when a second domain shows up, it lives as a sibling module with its own companion doc, not a section in an existing one.
