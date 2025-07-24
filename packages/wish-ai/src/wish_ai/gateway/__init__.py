"""
Gateway module for LLM API integrations.

This module provides abstract interfaces and concrete implementations
for connecting to various LLM providers.
"""

from .base import LLMGateway
from .openai import OpenAIGateway

__all__ = [
    "LLMGateway",
    "OpenAIGateway",
]
