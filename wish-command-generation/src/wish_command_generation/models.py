"""Models for the command generation client."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class GeneratedCommand(BaseModel):
    """Class representing a generated shell command."""

    command: str = Field(description="The generated shell command")
    """The generated shell command string."""

    explanation: str = Field(description="Explanation of what the command does")
    """Explanation of what the command does and why it was chosen."""


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

    error: Optional[str] = None
    """Error message if an error occurred during processing."""
