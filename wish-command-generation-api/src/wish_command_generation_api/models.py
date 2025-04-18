"""Models for the command generation graph."""

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class GeneratedCommand(BaseModel):
    """Class representing a generated shell command."""

    command: str = Field(description="The generated shell command")
    """The generated shell command string."""

    explanation: str = Field(description="Explanation of what the command does")
    """Explanation of what the command does and why it was chosen."""


class GraphState(BaseModel):
    """Class representing the state of LangGraph.

    This class is used to maintain state during LangGraph execution and pass data between nodes.
    wish-command-generation-api takes a query and context and outputs a generated command.
    """

    # Input fields - treated as read-only
    query: str = Field(description="User query for command generation")
    """The user's natural language query for command generation."""

    context: Dict[str, Any] = Field(default_factory=dict, description="Context for command generation")
    """Context information for command generation, such as current directory, history, etc."""

    # Intermediate result fields - no Annotated for serial execution
    processed_query: str | None = None
    """Processed and normalized user query."""

    command_candidates: List[str] | None = None
    """List of candidate commands generated."""

    # Final output field
    generated_command: GeneratedCommand | None = None
    """The final generated command with explanation. This is the output of the graph."""

    # Error flag
    api_error: bool = False
    """Flag indicating whether an API error occurred during processing."""


class GenerateRequest(BaseModel):
    """Request model for the generate endpoint."""

    query: str = Field(description="User query for command generation")
    """The user's natural language query for command generation."""

    context: Dict[str, Any] = Field(default_factory=dict, description="Context for command generation")
    """Context information for command generation, such as current directory, history, etc."""


class GenerateResponse(BaseModel):
    """Response model for the generate endpoint."""

    generated_command: GeneratedCommand
    """The generated command with explanation."""

    error: str | None = None
    """Error message if an error occurred during processing."""
