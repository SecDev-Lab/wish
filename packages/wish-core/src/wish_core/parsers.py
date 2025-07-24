"""Parser registry and base classes for wish-core."""

from abc import ABC, abstractmethod

from wish_models import Finding, Host, Service


class ToolParser(ABC):
    """Abstract base class for tool output parsers."""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """The name of the tool this parser handles."""
        pass

    @abstractmethod
    def can_parse(self, output: str, format_hint: str | None = None) -> bool:
        """Check if this parser can handle the given output."""
        pass

    @abstractmethod
    def parse_hosts(self, output: str) -> list[Host]:
        """Parse host information from tool output."""
        pass

    @abstractmethod
    def parse_services(self, output: str) -> list[Service]:
        """Parse service information from tool output."""
        pass

    @abstractmethod
    def parse_findings(self, output: str) -> list[Finding]:
        """Parse findings from tool output."""
        pass


class ParserRegistry:
    """Registry for tool parsers."""

    def __init__(self) -> None:
        self._parsers: dict[str, ToolParser] = {}

    def register(self, parser: ToolParser) -> None:
        """Register a parser for a tool."""
        self._parsers[parser.tool_name] = parser

    def get_parser(self, tool_name: str) -> ToolParser | None:
        """Get a parser for the specified tool."""
        return self._parsers.get(tool_name)

    def find_parser(self, output: str, format_hint: str | None = None) -> ToolParser | None:
        """Find a parser that can handle the given output."""
        for parser in self._parsers.values():
            if parser.can_parse(output, format_hint):
                return parser
        return None

    def list_tools(self) -> list[str]:
        """List all registered tool names."""
        return list(self._parsers.keys())
