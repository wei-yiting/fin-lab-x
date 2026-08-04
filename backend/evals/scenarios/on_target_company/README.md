# on_target_company

> **Dataset provenance**: the 8 cases (OTC-01…OTC-08) are copied from the
> language_policy dataset (LP-01…LP-08), keeping only the columns this
> scenario asserts on (`id`, `description`, `prompt`, `ticker`). Generating a
> dedicated dataset and retiring these seed cases is owned by DEV-96.

Measures whether the agent's answer stays on the company the user asked
about. One binary-rubric LLM judge (`on_target_company`, rubric in
[rubric.md](rubric.md)) applies a functional criterion: content about other
companies or the broader market passes only when it directly supports the
answer (peer comparison, market context); any other-company content that
stands on its own fails, regardless of length.

History: this judge started life inside language_policy as
`response_relevance` — a wrong name (it never measured language policy), and
a length-based rubric that could fail legitimate brief peer comparisons. It
was renamed, narrowed to the functional criterion, and moved here as its own
scenario (DEV-117).

Out of scope: topic drift about the *same* company (answering something the
user did not ask about {{expected.ticker}} itself) is not judged here.

## Gate

`regression.enabled: true` — the judge gates with the defaults (counted in,
`metric_floor` 1.0: every case must score Y). If measured runs show judge
flakiness once LLM-judge execution is repaired (DEV-120), lower the floor
with evidence, not preemptively.

Calibration debt: this judge has not been validated against human-labeled
ground truth (design-envelope §4 eval zone). The labels belong with the
dedicated dataset work — DEV-96 owns producing them alongside the
replacement dataset.
