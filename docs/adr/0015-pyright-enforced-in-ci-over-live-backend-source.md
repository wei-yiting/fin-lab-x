# ADR-0015: Pyright is enforced in CI over all live backend source (2026-08-18)

**Decision**: pyright runs over all live backend source — `include = ["backend"]`,
`typeCheckingMode = "standard"` — and a `Type check` step in CI's lint job makes
it a hard gate. `backend/tests` is the only exclusion, with its lifting
condition recorded next to it in `pyproject.toml`. The frozen `_html` pipeline
trees and `backend/common/sec_core.py` are checked like any other live source:
the A/B freeze covers the experimental variables — fetch, parse, embed, and the
public signatures the comparison is measured on — not type annotations. Their 43
errors cleared with annotations, `typing.cast`, and one import-path change, none
of which touch runtime behaviour.

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

**Rejected — adopt at full scope (no exclusions)**: only `backend/tests`
separates the gate from full scope, so the argument is now about the test tree
alone. Test doubles are deliberately not the types they stand in for — a
`FakeTenK` is not a `TenK`, a `@tool` object is not statically callable — and
fixtures unpack heterogeneous JSON as `**kwargs`; satisfying the checker there
means TypedDicts and casts scattered through the suite, noise traded for a green
tick. Unlike the frozen trees, whose fixes were type-level and free at runtime,
these would reshape the suite.

**Rejected — strict mode**: measured on this same scope, `strict` reports 567
diagnostics where `standard` reports zero, and roughly three in four are
unknown-type propagation from dependencies that ship no stubs (edgartools,
finnhub, tavily, autoevals, pandas). Those originate outside our own code and no
annotation of ours retires them, so the gate would be gated on upstream stub
coverage. `standard` is the baseline enforceable on day one; **reopen** `strict`
for a sub-path once its dependencies carry types.

**Why**: the gate is the point, not the 51 errors it happened to clear. Fixing the individual
defects without installing a gate treats symptoms and leaves nothing in place
to stop the next one. The adoption also corrects an asymmetry: CI's frontend
job already type-checks (`tsc -b`) and the backend did not, so identical
classes of error were caught on one side of the repo and not the other. Holding
the frozen trees to the checker works only because every fix there was
type-level; an error there needing a guard or a moved statement must be refused
and left open, not forced — the A/B baseline outranks a green tick.
`pythonVersion = "3.11"` pins the checker to `requires-python` so the gate does
not silently accept 3.13-only APIs just because CI installs 3.13. **Reopen
when** a type error reaches production that only the test tree would have
caught — the trigger to revisit `backend/tests` — or when a frozen-tree error
appears that no type-level fix reaches, which is the signal that the gate and
the A/B freeze have genuinely collided rather than merely looked like it.
