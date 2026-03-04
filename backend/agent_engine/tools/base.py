"""Base classes for FinLab-X tools."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar
from pydantic import BaseModel


InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT")


class BaseTool(ABC):
    """Base class for all FinLab-X tools."""

    name: str
    description: str
    input_schema: type[BaseModel]

    @abstractmethod
    def execute(self, input_data: InputT) -> OutputT:
        """Execute the tool with validated input.

        Args:
            input_data: Validated input data

        Returns:
            Tool execution result
        """
        pass

    def __call__(self, **kwargs) -> Any:
        """Allow tool to be called as a function.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool execution result
        """
        validated_input = self.input_schema(**kwargs)
        return self.execute(validated_input)
