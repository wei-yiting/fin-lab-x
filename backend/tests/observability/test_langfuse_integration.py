"""Langfuse SDK integration smoke tests.

Verify the SDK is installed correctly and import paths work.
No live Langfuse server needed — SDK gracefully handles missing env vars.
"""


def test_observe_decorator_importable_and_callable():
    from langfuse import observe

    @observe(name="smoke_test")
    def sample_fn(x: int) -> int:
        return x * 2

    result = sample_fn(5)
    assert result == 10


def test_callback_handler_instantiable():
    from langfuse.langchain import CallbackHandler

    handler = CallbackHandler()
    assert handler is not None
