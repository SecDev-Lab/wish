"""Models for the log analysis graph."""

from pydantic import BaseModel, Field
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState


class GraphState(BaseModel):
    """Class representing the state of LangGraph.

    This class is used to maintain state during LangGraph execution and pass data between nodes.
    wish-log-analysis takes a CommandResult object with None fields and outputs a CommandResult
    with all fields filled.
    """

    # Input field - treated as read-only
    command_result: CommandResult = Field(description="Input command result to be processed")
    """The CommandResult object to be processed. May have None fields for stdout, stderr."""

    # Intermediate result fields - no Annotated for serial execution
    log_summary: str | None = None
    """Summary of the log. Used to improve readability of the command result."""

    command_state: CommandState | None = None
    """Classification of the command result (SUCCESS, COMMAND_NOT_FOUND, etc.)."""

    # Final output field
    analyzed_command_result: CommandResult | None = None
    """The final CommandResult object with all fields filled. This is the output of the graph."""

    # Error flag
    api_error: bool = False
    """Flag indicating whether an API error occurred during processing."""
