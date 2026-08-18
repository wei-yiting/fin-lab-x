# ADR-0015: Pyright is adopted at narrow scope and enforced in CI (2026-08-18)

**Decision**: pyright runs at narrow scope — `include = ["backend"]`,
`typeCheckingMode = "standard"` — and a `Type check` step in CI's lint job makes
it a hard gate. `backend/tests`, the two frozen `_html` pipeline trees, and
`backend/common/sec_core.py` are excluded, each with its lifting condition
recorded next to the exclusion in `pyproject.toml`.

**Rejected — remove the dependency**: pyright was already installed but
unconfigured and un-run; invoked as-is it reported 175 errors with no way to
tell which ones mattered, which is indistinguishable from not having it. But
removing it would mean the three structural defects it surfaced — a
two-variable invariant, an asymmetric guard, and a sanitizer bypass — would
have had no mechanism to find them, and no successor mechanism was on offer.

**Rejected — keep the status quo (installed, unconfigured, not in CI)**: the
tool stays available for anyone who wants it, at zero adoption cost. The cost
is paid repeatedly instead of once: every person who runs it manually has to
re-derive which of the 175 errors are ignorable, and nothing stops a real error
from merging in the meantime.

**Rejected — adopt at full scope (no exclusions)**: the honest version of the
gate, and the one that needs no explaining. It is not reachable from here. CI
would be red on day one, and turning it green would require either editing code
`AGENTS.md` freezes (the `_html` A/B baseline and `sec_core.py`) or scattering
TypedDicts and casts through the test suite to satisfy test doubles that are
deliberately not the types they stand in for — noise traded for a green tick.

**Rejected — strict mode**: measured on this same narrow scope, `strict`
reports 340 diagnostics where `standard` reports zero, and roughly four in five
are unknown-type propagation from dependencies that ship no stubs (edgartools,
finnhub, tavily, autoevals, pandas). That is the same noise traded for a green
tick the exclusion list exists to avoid, paid before the gate could be switched
on at all. `standard` is the baseline enforceable on day one; **reopen** `strict`
— plausibly for a narrower sub-path — once the frozen tree is gone.

**Why**: the gate is the point, not the eight errors. Fixing the individual
defects without installing a gate treats symptoms and leaves nothing in place
to stop the next one. The adoption also corrects an asymmetry: CI's frontend
job already type-checks (`tsc -b`) and the backend did not, so identical
classes of error were caught on one side of the repo and not the other. What
the gate covers should be read narrowly: live, editable backend source only.
`sec_core.py` is a live module excluded because it is frozen, not because it is
clean — "pyright is green" is a weaker statement than it sounds, and the
exclusion list is the part worth reading. `pythonVersion = "3.11"` pins the
checker to `requires-python` so the gate does not silently accept 3.13-only
APIs just because CI installs 3.13. **Reopen when** the frozen `_html` tree and
`sec_core.py` are deleted at sunset — both exclusions go with them — or when a
type error reaches production that only the test tree would have caught, which
is the trigger to revisit the `backend/tests` exclusion.
