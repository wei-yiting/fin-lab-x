# ADR-0011: Repo-anchored data path configuration (2026-08-06)

**Decision**: every data path resolves through a resolver function in
`backend/common/config.py`, anchored off that module's own file location
via `Path(__file__)` — never off the process's CWD. Each resolver is
env-overridable (e.g. `DUCKDB_PATH`, `SEC_TEXT_DIR`) and defaults under
`<repo>/data/`, so a fresh clone works with zero setup. Rule going
forward: a new data location means a new resolver here, same shape;
consumers import the resolver and never construct `data/...` paths
themselves.

**Context**: CWD-relative defaults silently created a second `data/`
root depending on launch directory (uvicorn vs CLI vs IDE), splitting
the write side from the JIT read side.

**Rejected — env-var fail-fast for unset paths** (raise
`ConfigurationError` when unset): pure friction in a single-developer
repo; repo-anchored defaults keep the zero-setup clone while env
override stays available for deploy.

**Rejected — document a required startup directory** ("always run from
repo root"): that convention *was* the bug — a path that only resolves
correctly from one CWD, rediscovered by every new entry point.

**Re-evaluate if**: containerization or deployment needs data outside
the repo tree as the norm, at which point env-first defaults may fit
better than repo-anchored ones.
