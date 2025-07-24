"""wish-tools: Tool integrations and parsers for wish"""

from .execution import ExecutionResult, ToolExecutor
from .parsers import NmapParser, ToolParser

__version__ = "0.1.0"

__all__ = [
    "ToolParser",
    "NmapParser",
    "ToolExecutor",
    "ExecutionResult",
]
