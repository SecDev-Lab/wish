"""Factory for GraphState objects."""

from typing import Optional

import factory
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState

from ..models import GraphState
from .command_result import CommandResultFactory


class GraphStateFactory(factory.Factory):
    """Factory for GraphState objects."""

    class Meta:
        model = GraphState

    command_result: CommandResult = factory.SubFactory(CommandResultFactory)
    log_summary: Optional[str] = None
    command_state: Optional[CommandState] = None
    analyzed_command_result: Optional[CommandResult] = None

    @classmethod
    def create_with_command_result(cls, command_result: CommandResult) -> GraphState:
        """Create a GraphState with the given CommandResult.

        Args:
            command_result: The CommandResult to include in the GraphState.

        Returns:
            GraphState object with the given CommandResult.
        """
        return cls(command_result=command_result)

    @classmethod
    def create_with_log_summary(cls, command_result: CommandResult, log_summary: str) -> GraphState:
        """Create a GraphState with the given CommandResult and log summary.

        Args:
            command_result: The CommandResult to include in the GraphState.
            log_summary: The log summary to include in the GraphState.

        Returns:
            GraphState object with the given CommandResult and log summary.
        """
        return cls(command_result=command_result, log_summary=log_summary)

    @classmethod
    def create_with_command_state(cls, command_result: CommandResult, command_state: CommandState) -> GraphState:
        """Create a GraphState with the given CommandResult and command state.

        Args:
            command_result: The CommandResult to include in the GraphState.
            command_state: The command state to include in the GraphState.

        Returns:
            GraphState object with the given CommandResult and command state.
        """
        return cls(command_result=command_result, command_state=command_state)

    @classmethod
    def create_complete(cls, command_result: CommandResult, log_summary: str,
                       command_state: CommandState, analyzed_command_result: CommandResult) -> GraphState:
        """Create a complete GraphState with all fields set.

        Args:
            command_result: The CommandResult to include in the GraphState.
            log_summary: The log summary to include in the GraphState.
            command_state: The command state to include in the GraphState.
            analyzed_command_result: The analyzed CommandResult to include in the GraphState.

        Returns:
            GraphState object with all fields set.
        """
        return cls(
            command_result=command_result,
            log_summary=log_summary,
            command_state=command_state,
            analyzed_command_result=analyzed_command_result
        )
