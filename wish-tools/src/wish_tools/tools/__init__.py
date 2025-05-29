"""
Wish Tools - Tool implementations.

This package contains the actual tool implementations that conform
to the wish tools framework interface.

Available tools:
- BashTool: Execute bash commands
- MsfconsoleTool: Metasploit Framework console
- NmapTool: Network exploration and security auditing

## Adding New Tools

To add a new tool:

1. Create a new Python file in this directory
2. Implement a class that inherits from BaseTool
3. The tool will be auto-discovered by the framework

Example:

```python
from wish_tools.framework.base import BaseTool, ToolMetadata, ToolCapability

class MyTool(BaseTool):
    def _build_metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="mytool",
            version="1.0.0",
            description="My custom tool",
            author="Me",
            category="custom",
            capabilities=[...],
            requirements=["mytool-binary"],
            tags=["custom"]
        )

    async def validate_availability(self):
        # Check if tool is available
        pass

    async def execute(self, command, context):
        # Execute the tool
        pass

    def generate_command(self, capability, parameters, context=None):
        # Generate command for LLM
        pass
```
"""

# Import all tools to make them available for auto-discovery
try:
    from .bash import BashTool
    from .msfconsole import MsfconsoleTool

    __all__ = ["BashTool", "MsfconsoleTool"]
except ImportError:
    # Graceful degradation if some tools can't be imported
    __all__ = []
