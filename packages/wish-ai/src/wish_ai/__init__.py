"""
wish-ai: LLM integration and plan generation for wish

This package provides LLM connectivity, plan generation, and context building
for the wish penetration testing command center.
"""

from .context import ContextBuilder, PromptTemplates
from .conversation import ConversationManager
from .gateway import LLMGateway, OpenAIGateway
from .planning import Plan, PlanGenerator, PlanStep

__all__ = [
    "LLMGateway",
    "OpenAIGateway",
    "PlanGenerator",
    "Plan",
    "PlanStep",
    "ContextBuilder",
    "PromptTemplates",
    "ConversationManager",
]

__version__ = "0.1.0"
