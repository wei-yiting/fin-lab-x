"""S-obs-09: autouse fixture clears any Braintrust global handler between tests.

These tests are order-sensitive: the second asserts that whatever the first
installed has been cleared before it runs.
"""

import pytest

pytest.importorskip("braintrust_langchain")

from braintrust_langchain import BraintrustCallbackHandler, set_global_handler
from braintrust_langchain.context import braintrust_callback_handler_var


def test_first_installs_handler():
    """Deliberately register a global handler to simulate a test touching the
    eval runner's `_init_platform_tracing()` path."""
    handler = BraintrustCallbackHandler()
    set_global_handler(handler)
    assert braintrust_callback_handler_var.get(None) is handler


def test_second_observes_no_leaked_handler():
    """Runs after `test_first_installs_handler`. The autouse fixture must
    have cleared the handler, so this test starts from a clean state."""
    assert braintrust_callback_handler_var.get(None) is None
