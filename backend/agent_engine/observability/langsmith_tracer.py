"""LangSmith tracing utilities for FinLab-X."""

from functools import wraps
from typing import Any, Callable, Optional
from langsmith.run_trees import RunTree


def trace_step(
    step_name: str, run_type: str = "chain", tags: Optional[list[str]] = None
) -> Callable:
    """Decorator to wrap execution steps with LangSmith tracing.

    Args:
        step_name: Name of the step for tracing
        run_type: Type of run (chain, tool, llm, etc.)
        tags: Optional tags for filtering in LangSmith

    Returns:
        Decorated function with tracing
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            run_tree = RunTree(
                name=step_name,
                run_type=run_type,
                inputs={"args": args, "kwargs": kwargs},
                tags=tags or [],
            )

            try:
                result = func(*args, **kwargs)
                run_tree.end(outputs={"result": result})
                run_tree.post()
                return result
            except Exception as e:
                run_tree.end(error=str(e))
                run_tree.post()
                raise

        return wrapper

    return decorator
