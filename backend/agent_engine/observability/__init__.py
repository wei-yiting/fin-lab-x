"""Langfuse observability integration for FinLab-X.

Tracing is handled by two mechanisms:
- CallbackHandler: Injected in Orchestrator.run()/arun() for automatic
  LangChain agent tracing (LLM calls, tool dispatch).
- @observe(): Applied directly on tool functions for deterministic code tracing.
  Import from langfuse: `from langfuse import observe`
"""
