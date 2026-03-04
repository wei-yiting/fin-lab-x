"""Version-agnostic Orchestrator for FinLab-X."""

from typing import Any
from langchain.chat_models import init_chat_model
from langchain_core.messages import ToolMessage

from backend.agent_engine.workflows.config_loader import VersionConfig
from backend.agent_engine.agents.specialized.registry import get_tools_by_names
from backend.agent_engine.observability.langsmith_tracer import trace_step


class Orchestrator:
    """Version-agnostic Orchestrator that loads capabilities from config.

    The Orchestrator is the central reasoning engine that:
    1. Loads tools based on version config
    2. Manages the LLM + tool calling loop
    3. Enforces zero hallucination policy
    4. Traces all steps via LangSmith
    """

    def __init__(self, config: VersionConfig):
        """Initialize Orchestrator with version configuration.

        Args:
            config: VersionConfig object defining available capabilities
        """
        self.config = config

        self.tools = get_tools_by_names(config.tools)

        self.model = init_chat_model(
            model=config.model.name, temperature=config.model.temperature
        ).bind_tools(self.tools)

        self.system_prompt = self._build_system_prompt()

        self.max_iterations = config.model.max_iterations

    def _build_system_prompt(self) -> str:
        """Build system prompt with zero hallucination policy.

        Returns:
            System prompt string
        """
        return """You are FinLab-X, a strict, data-driven financial AI Agent.

ZERO HALLUCINATION POLICY:
- Only use data from provided tools
- If data is insufficient, say "I don't have enough information"
- Never invent financial metrics or news

TOOL USAGE:
- Use yfinance_stock_quote for current stock prices and metrics
- Use yfinance_get_available_fields to discover available data fields
- Use tavily_financial_search for recent news and sentiment
- Use sec_official_docs_retriever for official SEC filings

RESPONSE FORMAT:
- Start with a clear conclusion
- Support with specific data points
- Cite sources (tool names)
- Flag any data quality issues"""

    @trace_step(step_name="orchestrator_run", tags=["component:orchestrator"])
    def run(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Execute orchestration loop with tool calling.

        Args:
            prompt: User prompt to process
            **kwargs: Additional arguments

        Returns:
            Dictionary with response, tool_outputs, iterations, and metadata
        """
        messages = [("system", self.system_prompt), ("human", prompt)]

        iteration = 0
        current_messages = messages
        tool_outputs = []

        while iteration < self.max_iterations:
            response = self.model.invoke(current_messages)

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]

                    tool_result = self._execute_tool(tool_name, tool_args)
                    tool_outputs.append(
                        {"tool": tool_name, "args": tool_args, "result": tool_result}
                    )

                    current_messages = list(current_messages) + [
                        response,
                        ToolMessage(
                            content=str(tool_result), tool_call_id=tool_call["id"]
                        ),
                    ]
            else:
                return {
                    "response": response.content,
                    "tool_outputs": tool_outputs,
                    "iterations": iteration + 1,
                    "model": self.config.model.name,
                    "version": self.config.version,
                }

            iteration += 1

        return {
            "response": "Max iterations reached without completion",
            "tool_outputs": tool_outputs,
            "iterations": iteration,
            "error": "max_iterations_exceeded",
        }

    def _execute_tool(self, tool_name: str, tool_args: dict) -> Any:
        """Execute a specific tool by name.

        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments to pass to the tool

        Returns:
            Tool execution result
        """
        for tool in self.tools:
            if tool.name == tool_name:
                return tool.invoke(tool_args)
        return f"Error: Tool '{tool_name}' not found"
