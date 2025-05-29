"""
Wish Tools - Extensible tool framework for penetration testing workflows.

This package provides a unified interface for various penetration testing tools,
allowing them to be used seamlessly within the wish framework.

## Quick Start

```python
from wish_tools.framework.registry import tool_registry
from wish_tools.framework.base import ToolContext

# Get available tools
tools = tool_registry.list_tools()

# Use a tool
tool = tool_registry.get_tool("bash")
context = ToolContext(working_directory="/tmp", run_id="test")
result = await tool.execute(command, context)
```

## Legacy Tools

The following legacy tools are available for backward compatibility:
- tool_step_trace: Step tracing functionality
- to_base64: Base64 encoding utility

These will be migrated to the new framework interface in future versions.
"""

from wish_tools.framework.registry import tool_registry

__version__ = "1.0.0"
__all__ = ["tool_registry"]

# Auto-discover and register tools
try:
    tool_registry.auto_discover_tools("wish_tools.tools")
except Exception:
    # Graceful degradation if auto-discovery fails
    pass
