"""
Tool registry for managing available tools.

This module provides the ToolRegistry class for registering, discovering,
and managing tools in the wish framework.
"""

import importlib
import pkgutil
from typing import Dict, List, Optional, Set, Type

from .base import BaseTool, DuplicateToolError, ToolMetadata, ToolNotFoundError, ToolRegistrationError


class ToolRegistry:
    """Registry for managing tools in the framework."""

    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}
        self._categories: Dict[str, Set[str]] = {}
        self._tags: Dict[str, Set[str]] = {}

    def register_tool(self, tool_class: Type[BaseTool], override: bool = False) -> None:
        """Register a tool class.

        Args:
            tool_class: The tool class to register
            override: Whether to override existing tool with same name

        Raises:
            DuplicateToolError: If tool already exists and override is False
            ToolRegistrationError: If tool class is invalid
        """
        # Create temporary instance to get metadata
        try:
            temp_instance = tool_class()
            metadata = temp_instance.metadata
        except Exception as e:
            raise ToolRegistrationError(f"Failed to instantiate tool: {e}") from e

        tool_name = metadata.name

        if tool_name in self._tools and not override:
            raise DuplicateToolError(f"Tool '{tool_name}' already registered")

        self._tools[tool_name] = tool_class

        # Update category index
        if metadata.category not in self._categories:
            self._categories[metadata.category] = set()
        self._categories[metadata.category].add(tool_name)

        # Update tag index
        for tag in metadata.tags:
            if tag not in self._tags:
                self._tags[tag] = set()
            self._tags[tag].add(tool_name)

    def get_tool(self, name: str, config: Optional[Dict] = None) -> BaseTool:
        """Get a tool instance by name.

        Args:
            name: Tool name
            config: Optional configuration for the tool

        Returns:
            Tool instance

        Raises:
            ToolNotFoundError: If tool not found
        """
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' not found")

        # Create instance if not cached or config provided
        cache_key = f"{name}_{hash(str(config))}" if config else name
        if cache_key not in self._instances:
            self._instances[cache_key] = self._tools[name](config)

        return self._instances[cache_key]

    def list_tools(self) -> List[ToolMetadata]:
        """List all registered tools."""
        tools = []
        for tool_class in self._tools.values():
            instance = tool_class()
            tools.append(instance.metadata)
        return tools

    def list_by_category(self, category: str) -> List[str]:
        """List tools by category."""
        return list(self._categories.get(category, []))

    def list_by_tag(self, tag: str) -> List[str]:
        """List tools by tag."""
        return list(self._tags.get(tag, []))

    def search_tools(self, query: str) -> List[ToolMetadata]:
        """Search tools by name, description, or tags."""
        query_lower = query.lower()
        results = []

        for tool_class in self._tools.values():
            instance = tool_class()
            metadata = instance.metadata

            # Search in name, description, and tags
            if (
                query_lower in metadata.name.lower()
                or query_lower in metadata.description.lower()
                or any(query_lower in tag.lower() for tag in metadata.tags)
            ):
                results.append(metadata)

        return results

    def auto_discover_tools(self, package_path: str = "wish_tools.tools") -> None:
        """Auto-discover and register tools from a package.

        Args:
            package_path: Python package path to search for tools
        """
        # Import the package
        try:
            package = importlib.import_module(package_path)
        except ImportError as e:
            raise ToolRegistrationError(f"Failed to import package '{package_path}': {e}") from e

        # Walk through all modules in the package
        for _, module_name, _ in pkgutil.walk_packages(package.__path__, prefix=package.__name__ + "."):
            try:
                module = importlib.import_module(module_name)

                # Look for BaseTool subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseTool) and attr is not BaseTool:
                        try:
                            self.register_tool(attr)
                        except DuplicateToolError:
                            # Skip duplicates during auto-discovery
                            pass
            except Exception:
                # Skip modules that fail to import
                continue

    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool.

        Args:
            name: Tool name to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if name not in self._tools:
            return False

        # Get metadata for cleanup
        instance = self._tools[name]()
        metadata = instance.metadata

        # Remove from main registry
        del self._tools[name]

        # Remove from instances cache
        keys_to_remove = [k for k in self._instances.keys() if k.startswith(name)]
        for key in keys_to_remove:
            del self._instances[key]

        # Remove from category index
        if metadata.category in self._categories:
            self._categories[metadata.category].discard(name)
            if not self._categories[metadata.category]:
                del self._categories[metadata.category]

        # Remove from tag index
        for tag in metadata.tags:
            if tag in self._tags:
                self._tags[tag].discard(name)
                if not self._tags[tag]:
                    del self._tags[tag]

        return True


# Global registry instance
tool_registry = ToolRegistry()
