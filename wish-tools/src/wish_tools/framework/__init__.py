"""
Wish Tools Framework - Core framework components for tool abstraction.

This module provides the base classes and utilities for implementing
tools in the wish framework.
"""

from .base import BaseTool, CommandInput, ToolCapability, ToolContext, ToolMetadata, ToolResult
from .registry import ToolRegistry, tool_registry
from .testing import TestCase, TestResult, ToolTester

__all__ = [
    "BaseTool",
    "CommandInput",
    "ToolMetadata",
    "ToolCapability",
    "ToolContext",
    "ToolResult",
    "ToolRegistry",
    "tool_registry",
    "ToolTester",
    "TestCase",
    "TestResult",
]
