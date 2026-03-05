"""Version-agnostic Orchestrator for FinLab-X.

Uses LangChain's create_agent to handle the tool calling loop automatically.
The Orchestrator does NOT manually manage bind_tools or tool execution —
create_agent handles tool schema binding and the ReAct loop internally.
"""

from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage

from backend.agent_engine.workflows.config_loader import VersionConfig
from backend.agent_engine.agents.specialized.registry import get_tools_by_names


class Orchestrator:
    """Version-agnostic Orchestrator that loads capabilities from config.

    The Orchestrator is the central reasoning engine that:
    1. Loads tools based on version config
    2. Delegates the tool calling loop to LangChain's create_agent
    3. Enforces zero hallucination policy via system prompt
    4. Integrates with LangSmith automatically (via LangChain internals)
    """

    def __init__(self, config: VersionConfig):
        """Initialize Orchestrator with version configuration.

        Args:
            config: VersionConfig object defining available capabilities
        """
        self.config = config
        self.tools = get_tools_by_names(config.tools)
        self.system_prompt = self._build_system_prompt()

        self.agent = create_agent(
            model=config.model.name,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt with zero hallucination policy.

        Tool descriptions are NOT listed here — create_agent passes tool
        schemas to the LLM automatically via bind_tools. The system prompt
        only defines behavioral policy and response format.

        Returns:
            System prompt string
        """
        return """You are FinLab-X, a strict, data-driven financial AI Agent.

ZERO HALLUCINATION POLICY:
- Only use data from provided tools
- If data is insufficient, say "I don't have enough information"
- Never invent financial metrics or news

RESPONSE FORMAT:
- Start with a clear conclusion
- Support with specific data points
- Cite sources (tool names)
- Flag any data quality issues"""

    def run(self, prompt: str, **kwargs) -> dict[str, Any]:
        """Execute the agent with a user prompt.

        Delegates tool calling loop to create_agent. Extracts response text
        and tool outputs from the agent's message history.

        Args:
            prompt: User prompt to process
            **kwargs: Additional arguments

        Returns:
            Dictionary with response, tool_outputs, and metadata
        """
        result = self.agent.invoke({"messages": [{"role": "user", "content": prompt}]})

        return self._extract_result(result)

    def _extract_result(self, agent_output: dict) -> dict[str, Any]:
        """Extract structured result from agent message history.

        Args:
            agent_output: Raw output from create_agent.invoke()

        Returns:
            Dictionary with response, tool_outputs, model, and version
        """
        messages = agent_output.get("messages", [])

        # Extract final AI response (last AIMessage without tool_calls)
        response_text = ""
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and not msg.tool_calls:
                response_text = msg.content
                break

        # Extract tool outputs from ToolMessages
        tool_outputs: list[dict[str, Any]] = []
        for i, msg in enumerate(messages):
            if isinstance(msg, ToolMessage):
                # Find the preceding AIMessage's tool_call for this ToolMessage
                tool_name = msg.name or "unknown"
                tool_args: dict[str, Any] = {}

                # Walk backwards to find the matching tool_call
                for prev_msg in reversed(messages[:i]):
                    if isinstance(prev_msg, AIMessage) and prev_msg.tool_calls:
                        for tc in prev_msg.tool_calls:
                            if tc.get("id") == msg.tool_call_id:
                                tool_name = tc["name"]
                                tool_args = tc["args"]
                                break
                        break

                tool_outputs.append(
                    {"tool": tool_name, "args": tool_args, "result": msg.content}
                )

        return {
            "response": response_text,
            "tool_outputs": tool_outputs,
            "model": self.config.model.name,
            "version": self.config.version,
        }
