"""
Base classes for tool output parsers
"""

from abc import ABC, abstractmethod
from typing import Any

from wish_models import Finding, Host, Service


class ToolParser(ABC):
    """Base class for parsing security tool outputs"""

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Name of the tool this parser handles"""

    @property
    @abstractmethod
    def supported_formats(self) -> list[str]:
        """List of supported output formats"""

    @abstractmethod
    def can_parse(self, output: str, format_hint: str | None = None) -> bool:
        """Check if this parser can handle the given output"""

    @abstractmethod
    def parse_hosts(self, output: str, format_hint: str | None = None) -> list[Host]:
        """Extract host information from tool output"""

    @abstractmethod
    def parse_services(self, output: str, format_hint: str | None = None) -> list[Service]:
        """Extract service information from tool output"""

    @abstractmethod
    def parse_findings(self, output: str, format_hint: str | None = None) -> list[Finding]:
        """Extract security findings from tool output"""

    def parse_all(
        self, output: str, format_hint: str | None = None
    ) -> dict[str, list[Host] | list[Service] | list[Finding]]:
        """Parse all available information from tool output"""
        return {
            "hosts": self.parse_hosts(output, format_hint),
            "services": self.parse_services(output, format_hint),
            "findings": self.parse_findings(output, format_hint),
        }

    def get_metadata(self, output: str, format_hint: str | None = None) -> dict[str, Any]:
        """Extract metadata from tool output (scan timing, arguments, etc.)"""
        return {}
