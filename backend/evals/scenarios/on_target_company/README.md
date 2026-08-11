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

Out of scope: topic drift about the *same* company (answering something the
user did not ask about {{expected.ticker}} itself) is not judged here.

## Gate

`regression.enabled: false` — no evaluation has been run yet, so there is no
measured baseline to set a `metric_floor` from. This judge is also
unvalidated against human-labeled ground truth (no TPR/TNR measured;
design-envelope §4 eval zone). Both are owned by DEV-96 alongside the
dedicated dataset work — flip to `true` once a first run establishes a
baseline and calibration exists.
