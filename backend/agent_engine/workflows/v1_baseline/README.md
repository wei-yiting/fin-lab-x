# v1 Baseline Workflow

## Folder Responsibility
Implements the naive v1 LLM chain: system prompt + user input + tool calling + final synthesis.

## File Manifest
- `__init__.py`: Workflow exports.
- `chain.py`: Naive chain implementation with tool execution.
- `prompts.py`: System prompt for the v1 baseline chain.

## Architecture & Design
- Linear execution: prompt -> LLM (tool calls) -> tool execution -> LLM synthesis.
- No conversation memory or state transitions.

## Implementation Guidelines
- Keep the system prompt local to this workflow.
- Always return explicit errors from tool failures.
- Prefer `invoke_with_debug` for manual verification scripts.
