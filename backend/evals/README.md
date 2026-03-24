# Evaluation Tests

Evaluation tests verify **agent behavior quality** against real LLM APIs. They serve a different purpose from the unit tests in `backend/tests/`:

| | Unit Tests (`backend/tests/`) | Evals (`backend/evals/`) |
|---|---|---|
| LLM | Mocked | Real API calls |
| Nature | Deterministic | Non-deterministic |
| Duration | < 2s | ~60s |
| When to run | CI (always) | Manual trigger |
| Purpose | Verify code logic | Verify agent behavior meets expectations |

## Running Evals

```bash
# Run evals only
uv run pytest -m eval -v --tb=short

# Run unit tests only (CI default)
uv run pytest -m "not eval"

# Run a specific scenario
uv run pytest -m eval -k "LP-01" -v

# Run everything (unit tests + evals)
uv run pytest -v
```

All eval test functions are marked with `@pytest.mark.eval`. Use `-m eval` / `-m "not eval"` to select or exclude them.

## Marker Convention

Every test function in `backend/evals/` **must** be decorated with `@pytest.mark.eval`:

```python
import pytest

@pytest.mark.eval
def test_something(orchestrator):
    ...
```

When combined with `@pytest.mark.parametrize`, the `eval` marker goes first:

```python
@pytest.mark.eval
@pytest.mark.parametrize("case", CASES, ids=[c.id for c in CASES])
def test_language_policy(orchestrator, case):
    ...
```

### Why this matters

The marker is what separates evals from unit tests at execution time. Without it, `pytest -m "not eval"` (the CI default) would pick up your eval test and try to run it — hitting real APIs, failing without keys, and slowing down the pipeline.

### Registration

The `eval` marker is registered in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = ["eval: evaluation tests that hit real LLM APIs"]
```

If you introduce a new marker (e.g., `eval_slow` for long-running evals), register it here to avoid pytest warnings.

## Prerequisites

Eval tests call real LLM and external APIs. The following environment variables must be set (in `backend/.env`):

- `OPENAI_API_KEY` — LLM calls
- `TAVILY_API_KEY` — News search eval cases
- `EDGAR_IDENTITY` — SEC filing retrieval eval cases

## Directory Structure

```
backend/evals/
├── README.md                 ← This file
├── __init__.py
├── eval_helpers.py           ← Language detection utils (CJK regex)
├── datasets/
│   ├── __init__.py
│   └── language_policy.py    ← Language Policy eval cases
├── conftest.py               ← Real Orchestrator fixture
└── test_language_policy.py   ← Language Policy eval tests
```

## Design Principles

1. **Separate eval datasets from test logic**: `datasets/` defines eval cases (input + expected output), `test_*.py` defines assertion logic. Adding new eval cases only requires modifying the dataset, not the test code.
2. **Prefer programmatic assertions**: Use regex and computation over LLM-as-judge whenever possible to minimize non-determinism.
3. **Before/After comparison**: Run evals before and after each prompt change, then diff the results to prove improvement.

## Assertion Strategies

### Programmatic (current)

Use regex, computation, or string matching when the check is structurally decidable — no ambiguity, no interpretation needed.

| Check | Method | Example |
|---|---|---|
| Response language | CJK character ratio | `cjk_ratio(response) >= 0.20` |
| Tool arg language | CJK presence | `not contains_cjk(query)` |
| Tool called | Check tool_outputs | `tool_output["tool"] == "tavily_financial_search"` |

### LLM-as-Judge (future guardrails)

For checks that require semantic understanding, use an LLM judge that returns a binary `PASS` / `FAIL: <reason>` verdict. This is not scoring — it is a guardrail that blocks unacceptable behavior.

A generic judge wrapper in `eval_helpers.py` would look like:

```python
from openai import OpenAI

def llm_judge(system_prompt: str, content: str) -> tuple[bool, str]:
    """Binary LLM judge. Returns (passed, verdict_text)."""
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
    )
    verdict = resp.choices[0].message.content.strip()
    passed = verdict.startswith("PASS")
    return passed, verdict
```

Then build specific guardrail judges on top of it:

```python
def judge_no_hallucination(response: str, tool_outputs: list[dict]) -> tuple[bool, str]:
    return llm_judge(
        system_prompt=(
            "You are a strict auditor. Check if the response ONLY uses "
            "data present in the tool outputs. No invented numbers, no "
            "fabricated facts. Reply 'PASS' or 'FAIL: <specific violation>'."
        ),
        content=f"Tool outputs:\n{tool_outputs}\n\nResponse:\n{response}",
    )
```

Used in a test exactly like programmatic assertions:

```python
@pytest.mark.eval
def test_no_hallucination(orchestrator, case):
    result = orchestrator.run(case.prompt)
    passed, reason = judge_no_hallucination(result["response"], result["tool_outputs"])
    assert passed, f"[{case.id}] Guardrail violated: {reason}"
```

### Candidate guardrails

| Guardrail | What it catches | Judge prompt focus |
|---|---|---|
| **No hallucination** | Agent invents data not present in tool outputs | Compare response claims against tool output data |
| **Source citation** | Agent fails to cite which tool provided the data | Check every factual claim has a source attribution |
| **Tool-response consistency** | Agent contradicts its own tool results | Detect conflicts between tool outputs and final response |
| **Scope adherence** | Agent answers beyond what was asked | Check response stays within the scope of the user's question |

### When to use which

```
Can you check it with string/regex/math?
  YES → Programmatic (deterministic, fast, free)
  NO  → Does it need semantic understanding?
        YES → LLM judge (non-deterministic, slower, costs API calls)
```

Prefer programmatic whenever possible. LLM judges add a second layer of non-determinism on top of the already non-deterministic agent output.

## Adding New Evals

1. Add or modify eval case definitions in `datasets/`
2. Add a corresponding parametrized test in `test_*.py` (or extend an existing dataset list)
3. Mark every test function with `@pytest.mark.eval`
4. Run `uv run pytest -m eval -v` to verify
