from unittest.mock import MagicMock

import pytest

from backend.agent_engine.agents.base import _HandleToolErrors
from backend.agent_engine.streaming.tool_error_sanitizer import sanitize_tool_error
from backend.common.sec_core import SectionNotFoundError, UnsupportedFilingTypeError
from backend.evals.experiments.tool_error_messages.run import (
    ARMS,
    arm_order,
    legacy_messages,
)

_RAW = (
    "Ticker ASML appears to be a foreign private issuer that files 20-F; "
    "only '10-K' is supported. key: api_key=sk-abcdef1234567890"
)


def _run_middleware(exc: Exception) -> str:
    request = MagicMock()
    request.tool_call = {
        "name": "sec_filing_list_sections",
        "args": {"ticker": "ASML"},
        "id": "c1",
        "type": "tool_call",
    }

    def handler(_request):
        raise exc

    return _HandleToolErrors().wrap_tool_call(request, handler).content


@pytest.mark.parametrize(
    "exc",
    [
        UnsupportedFilingTypeError(_RAW),
        SectionNotFoundError("Section '7' not found.", available_keys=("1",)),
        RuntimeError("boom at /srv/app/internal/thing.py"),
    ],
)
def test_before_arm_reproduces_pre_contract_middleware_text(exc):
    with legacy_messages():
        assert _run_middleware(exc) == sanitize_tool_error(str(exc))


def test_after_arm_uses_the_contract():
    assert _run_middleware(UnsupportedFilingTypeError(_RAW)).startswith(
        "TOOL ERROR — kind: non_10k_filer"
    )


def test_arms_share_config_and_prompt():
    assert ARMS["before"].config_dir == ARMS["after"].config_dir
    assert ARMS["before"].prompt_path == ARMS["after"].prompt_path


def test_arm_order_alternates_by_row_and_rep():
    assert arm_order(0, 2) == ["before", "after"]
    assert arm_order(1, 2) == ["after", "before"]
    assert arm_order(0, 1) == ["after", "before"]
