from __future__ import annotations

from typing import Iterable

from backend.agent_engine.workflows.v1_baseline.chain import create_naive_chain


def _print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_tool_outputs(tool_outputs: Iterable[dict[str, object]]) -> None:
    if not tool_outputs:
        print("Tool Calls: None")
        return

    print("Tool Calls:")
    for output in tool_outputs:
        print(f"- {output.get('name')}")
        print(f"  args: {output.get('args')}")
        print(f"  result: {output.get('result')}")


def main() -> None:
    chain = create_naive_chain()
    test_cases = [
        {
            "name": "Test Case 1: Stock Price",
            "prompt": "What is the current price of AAPL?",
        },
        {
            "name": "Test Case 2: Official Risks",
            "prompt": "What are the main risk factors for TSLA?",
        },
        {
            "name": "Test Case 3: Recent News",
            "prompt": "Why did NVDA stock jump today?",
        },
        {
            "name": "Test Case 4: Hybrid",
            "prompt": "Compare AAPL price and its latest official risks.",
        },
    ]

    for test_case in test_cases:
        _print_section(test_case["name"])
        debug = chain.invoke_with_debug(test_case["prompt"])
        _print_tool_outputs(debug.tool_outputs)
        print("Response:")
        print(debug.response)


if __name__ == "__main__":
    main()
