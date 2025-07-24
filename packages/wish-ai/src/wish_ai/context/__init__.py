"""
Context building module for AI prompt construction.

This module provides functionality for building rich context information
that is used to construct effective prompts for LLM interactions.
"""

from .builder import ContextBuilder
from .templates import PromptTemplates

__all__ = [
    "ContextBuilder",
    "PromptTemplates",
]
