"""Evaluation tests for language policy compliance.

BDD scenarios verifying:
  Rule A — Tool arguments (search queries) are always in English
  Rule B — Response language matches the user's prompt language
"""

import re

import pytest

from backend.evals.datasets.language_policy import LANGUAGE_POLICY_CASES
from backend.evals.eval_helpers import cjk_ratio, contains_cjk


@pytest.mark.eval
@pytest.mark.parametrize(
    "case",
    LANGUAGE_POLICY_CASES,
    ids=[c.id for c in LANGUAGE_POLICY_CASES],
)
def test_language_policy(orchestrator, case):
    result = orchestrator.run(case.prompt)

    # Rule A: tool arguments must not contain CJK characters
    if case.expect_search_query_no_cjk:
        matched_expected_tool = False
        for tool_output in result["tool_outputs"]:
            if case.expect_tool and tool_output["tool"] != case.expect_tool:
                continue
            if case.expect_tool:
                matched_expected_tool = True
            for arg_key, arg_val in tool_output["args"].items():
                if not isinstance(arg_val, str):
                    continue
                if arg_key == "ticker":
                    assert re.match(r"^[A-Z][A-Z0-9.\-]*$", arg_val), (
                        f"[{case.id}] Tool '{tool_output['tool']}' arg 'ticker' "
                        f"is not a valid ticker format: '{arg_val}'"
                    )
                    continue
                assert not contains_cjk(arg_val), (
                    f"[{case.id}] Tool '{tool_output['tool']}' arg '{arg_key}' "
                    f"contains CJK: '{arg_val}'"
                )
        if case.expect_tool:
            assert matched_expected_tool, (
                f"[{case.id}] Expected tool '{case.expect_tool}' was never called. "
                f"Tools called: {[t['tool'] for t in result['tool_outputs']]}"
            )

    # Rule B: response language matches prompt language
    ratio = cjk_ratio(result["response"])
    assert ratio >= case.expect_response_cjk_min, (
        f"[{case.id}] Response CJK ratio {ratio:.3f} < "
        f"expected min {case.expect_response_cjk_min} "
        f"(prompt_lang={case.prompt_language})"
    )
    assert ratio <= case.expect_response_cjk_max, (
        f"[{case.id}] Response CJK ratio {ratio:.3f} > "
        f"expected max {case.expect_response_cjk_max} "
        f"(prompt_lang={case.prompt_language})"
    )
