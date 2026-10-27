"""Tests for the prompt x tool 2x2: run order, config-layout gate, analysis."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from backend.evals.experiments.prompt_tool_2x2.analyze import (
    arm_tools,
    factorial,
    run_metrics,
    sign_test,
)
from backend.evals.experiments.prompt_tool_2x2.run import (
    ARM_A,
    ARM_B,
    ARM_C,
    ARM_D,
    arm_order,
    check_factorial,
)
from backend.evals.experiments.tool_selection.analyze import load_labels

LABELS = Path(__file__).parent / "fixtures" / "tool_routing_labels_sample.csv"
BASE_TOOLS = [
    "finnhub_stock_quote",
    "finnhub_company_basic_financials",
    "tavily_financial_search",
    "sec_filing_list_sections",
    "sec_filing_get_section",
]
SEARCH = "sec_filing_search"


def test_arm_order_is_williams_balanced() -> None:
    orders = [arm_order(position, rep=0) for position in range(4)]

    for slot in range(4):
        assert {order[slot] for order in orders} == {ARM_A, ARM_B, ARM_C, ARM_D}
    adjacent = Counter(
        (order[i], order[i + 1]) for order in orders for i in range(len(order) - 1)
    )
    assert len(adjacent) == 12
    assert set(adjacent.values()) == {1}


def test_arm_order_rotates_with_repetition() -> None:
    assert arm_order(0, rep=1) == arm_order(1, rep=0)


def resolved(tools: list[str], prompt: str) -> dict[str, Any]:
    return {
        "arm": "x",
        "identity": {"name": "x"},
        "config_model": {"name": "openai:gpt-5.6-luna"},
        "constraints": {"max_tool_calls_per_run": 10},
        "tools": tools,
        "tool_contracts": {t: {"description_sha256": t} for t in tools},
        "prompt": {"raw_sha256": prompt},
    }


def designed() -> dict[str, dict[str, Any]]:
    return {
        ARM_A: resolved(BASE_TOOLS, "baseline"),
        ARM_B: resolved([*BASE_TOOLS, SEARCH], "reader"),
        ARM_C: resolved([*BASE_TOOLS, SEARCH], "baseline"),
        ARM_D: resolved(BASE_TOOLS, "reader"),
    }


def test_check_factorial_passes_the_designed_layout() -> None:
    check = check_factorial(designed())

    assert check["ok"]
    assert check["layout_errors"] == []


def test_check_factorial_rejects_a_cell_with_the_wrong_prompt() -> None:
    arms = designed()
    arms[ARM_C] = resolved([*BASE_TOOLS, SEARCH], "reader")

    check = check_factorial(arms)

    assert not check["ok"]
    assert any(ARM_C in e for e in check["layout_errors"])


def test_check_factorial_rejects_a_difference_outside_tools_and_prompt() -> None:
    arms = designed()
    arms[ARM_D]["constraints"] = {"max_tool_calls_per_run": 20}

    check = check_factorial(arms)

    assert not check["ok"]
    assert check["vs_control"][ARM_D]["unexpected_differences"] == ["constraints"]


def call(tool: str, ticker: str, error: str | None = None) -> dict[str, Any]:
    out: dict[str, Any] = {"tool": tool, "args": {"ticker": ticker}}
    if error is None:
        out["result"] = "{}"
    else:
        out["error"] = error
    return out


def record(row_id: str, arm: str, calls: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "row_id": row_id,
        "arm": arm,
        "repetition": 1,
        "slot_in_row": 0,
        "started_at": "",
        "finished_at": "",
        "task_error": None,
        "output": {"response": "", "tool_outputs": calls, "model": "openai:x"},
        "scores": {"diagnostic_execution_health": 1.0},
        "score_details": {},
        "llm_calls": [],
    }


@pytest.fixture(scope="module")
def tools() -> dict[str, set[str]]:
    return arm_tools()


def test_unknown_tool_attempt_counts_as_consulting_sec_but_not_success(
    tools: dict[str, set[str]],
) -> None:
    sheet = load_labels(LABELS)
    calls = [
        call("tavily_financial_search", "TSLA"),
        call(SEARCH, "TSLA", error=f"Error: {SEARCH} is not a valid tool"),
    ]

    row = run_metrics(record("1", ARM_D, calls), sheet, tools)

    assert row["unknown_tool_calls"] == 1
    assert row["unknown_tools"] == SEARCH
    assert row["sec_required"] is True
    assert row["sec_skip"] is False
    assert row["sec_skip_no_success"] is True


def test_the_same_call_is_known_in_an_arm_that_has_search(
    tools: dict[str, set[str]],
) -> None:
    sheet = load_labels(LABELS)

    row = run_metrics(record("1", ARM_C, [call(SEARCH, "TSLA")]), sheet, tools)

    assert row["unknown_tool_calls"] == 0
    assert row["sec_skip"] is False
    assert row["sec_skip_no_success"] is False


def test_sec_skip_is_only_defined_on_reachable_sec_required_rows(
    tools: dict[str, set[str]],
) -> None:
    sheet = load_labels(LABELS)

    skipped = run_metrics(
        record("1", ARM_A, [call("tavily_financial_search", "TSLA")]), sheet, tools
    )
    full_gap = run_metrics(record("4", ARM_A, []), sheet, tools)

    assert skipped["sec_skip"] is True
    assert skipped["sec_skip_at_budget"] is False
    assert full_gap["sec_required"] is False
    assert full_gap["sec_skip"] == ""


def test_factorial_effects_and_interaction() -> None:
    # Row 1: tool adds 2 under either prompt, prompt adds 1 -> no interaction.
    # Row 2: the tool only works with the reader prompt -> interaction 4.
    cells = {
        "1": {ARM_A: 0, ARM_C: 2, ARM_D: 1, ARM_B: 3},
        "2": {ARM_A: 0, ARM_C: 0, ARM_D: 0, ARM_B: 4},
    }
    rows = [
        {"row_id": rid, "arm": arm, "e2e_s": value}
        for rid, by_arm in cells.items()
        for arm, value in by_arm.items()
    ]
    rows.append({"row_id": "3", "arm": ARM_A, "e2e_s": 9.0})

    effects = factorial(
        [
            {
                **r,
                **{
                    k: ""
                    for k in (
                        "recall",
                        "unnecessary",
                        "sec_skip",
                        "sec_skip_no_success",
                        "sec_evidence_tokens",
                        "tool_calls_total",
                        "est_cost_usd",
                    )
                },
                "sec_required": False,
            }
            for r in rows
        ]
    )["e2e_s"]

    assert effects["rows"] == 2
    assert effects["**tool main effect**"][0] == pytest.approx((2 + 2) / 2)
    assert effects["**prompt main effect**"][0] == pytest.approx((1 + 2) / 2)
    assert effects["**interaction**"][0] == pytest.approx((0 + 4) / 2)
    assert effects["bundle (B − A)"][0] == pytest.approx((3 + 4) / 2)


def test_routing_effects_leave_out_full_coverage_gap_rows(
    tools: dict[str, set[str]],
) -> None:
    sheet = load_labels(LABELS)
    news = call("tavily_financial_search", "TSLA")
    rows = [
        run_metrics(record(rid, arm, [news]), sheet, tools)
        for rid in ("1", "4")
        for arm in (ARM_A, ARM_B, ARM_C, ARM_D)
    ]

    effects = factorial(rows)

    assert effects["recall"]["rows"] == 1
    assert effects["sec_skip"]["rows"] == 1
    assert effects["e2e_s"]["rows"] == 0


def test_sign_test_drops_ties_and_is_two_sided() -> None:
    assert sign_test([-1.0, -2.0, -0.5, -3.0, -1.0, 0.0, 0.0]) == (5, 0, 0.0625)
    assert sign_test([0.0, 0.0]) == (0, 0, 1.0)
    assert sign_test([-1.0, 1.0])[2] == 1.0
