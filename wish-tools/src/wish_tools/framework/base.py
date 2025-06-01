"""
Base classes for the wish tools framework.

This module provides the abstract base classes and data models
that all tools must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCapability(BaseModel):
    """Describes a specific capability of a tool."""

    name: str = Field(description="Name of the capability")
    description: str = Field(description="Description of what this capability does")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for this capability")
    examples: List[str] = Field(default_factory=list, description="Example commands")


class ToolMetadata(BaseModel):
    """Metadata for a tool."""

    name: str = Field(description="Tool name")
    version: str = Field(description="Tool version")
    description: str = Field(description="Tool description")
    author: str = Field(description="Tool author")
    category: str = Field(description="Tool category (e.g., 'network', 'exploitation', 'general')")
    capabilities: List[ToolCapability] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list, description="System requirements")
    tags: List[str] = Field(default_factory=list, description="Tags for tool discovery")


class ToolContext(BaseModel):
    """Context passed to tools during execution."""

    working_directory: str
    environment_variables: Dict[str, str] = Field(default_factory=dict)
    system_info: Optional[Dict[str, Any]] = None
    run_id: Optional[str] = None
    timeout_override: Optional[int] = None


class CommandInput(BaseModel):
    """Input command for tool execution."""

    command: str = Field(description="The command to execute")
    timeout_sec: int = Field(default=300, description="Timeout in seconds")
    tool_parameters: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")


class ToolResult(BaseModel):
    """Result from tool execution."""

    success: bool = Field(description="Whether execution was successful")
    output: str = Field(description="Standard output from the command")
    error: Optional[str] = Field(default=None, description="Error output if any")
    exit_code: int = Field(description="Exit code from the command")
    execution_time: float = Field(description="Execution time in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """Abstract base class for all tools in the framework."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the tool with optional configuration."""
        self.config = config or {}
        self._metadata = self._build_metadata()

    @abstractmethod
    def _build_metadata(self) -> ToolMetadata:
        """Build and return tool metadata."""
        pass

    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self._metadata

    @abstractmethod
    async def validate_availability(self) -> tuple[bool, Optional[str]]:
        """Check if the tool is available on the system.

        Returns:
            Tuple of (is_available, error_message)
        """
        pass

    @abstractmethod
    async def execute(self, command: CommandInput, context: ToolContext, **kwargs) -> ToolResult:
        """Execute a command using this tool.

        Args:
            command: The command to execute
            context: Execution context
            **kwargs: Additional tool-specific arguments

        Returns:
            ToolResult containing execution results
        """
        pass

    @abstractmethod
    def generate_command(
        self, capability: str, parameters: Dict[str, Any], context: Optional[ToolContext] = None
    ) -> CommandInput:
        """Generate a command for a specific capability.

        Args:
            capability: The capability to use
            parameters: Parameters for the capability
            context: Optional execution context

        Returns:
            Generated CommandInput
        """
        pass

    def get_documentation(self) -> str:
        """Generate comprehensive documentation for this tool."""
        doc_parts = [
            f"# {self.metadata.name}",
            f"\n{self.metadata.description}",
            f"\n**Version:** {self.metadata.version}",
            f"**Author:** {self.metadata.author}",
            f"**Category:** {self.metadata.category}",
            f"**Tags:** {', '.join(self.metadata.tags)}",
            "\n## Requirements",
            "\n".join(f"- {req}" for req in self.metadata.requirements),
            "\n## Capabilities",
        ]

        for cap in self.metadata.capabilities:
            doc_parts.extend([f"\n### {cap.name}", f"{cap.description}", "\n**Parameters:**"])
            for param, details in cap.parameters.items():
                doc_parts.append(f"- `{param}`: {details}")

            if cap.examples:
                doc_parts.append("\n**Examples:**")
                for example in cap.examples:
                    doc_parts.append(f"```bash\n{example}\n```")

        return "\n".join(doc_parts)

    def validate_command(self, command: CommandInput) -> tuple[bool, Optional[str]]:
        """Validate if a command can be executed by this tool.

        Args:
            command: The command to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Default implementation - can be overridden by specific tools
        return True, None


class ToolException(Exception):
    """Base exception for tool-related errors."""

    pass


class ToolNotFoundError(ToolException):
    """Raised when a requested tool is not found."""

    pass


class ToolRegistrationError(ToolException):
    """Raised when tool registration fails."""

    pass


class DuplicateToolError(ToolException):
    """Raised when attempting to register a duplicate tool."""

    pass


class ToolExecutionError(ToolException):
    """Raised when tool execution fails."""

    pass
