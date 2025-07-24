"""
wish-core: Business logic and state management for wish

This package provides state management, event handling, and core business logic
for the wish penetration testing command center.
"""

from .config import ConfigManager, WishConfig
from .events import EngagementEvent, EventBus
from .parsers import ParserRegistry, ToolParser
from .session import SessionManager
from .state import InMemoryStateManager, StateManager

__all__ = [
    "StateManager",
    "InMemoryStateManager",
    "EngagementEvent",
    "EventBus",
    "SessionManager",
    "ParserRegistry",
    "ToolParser",
    "ConfigManager",
    "WishConfig",
]

__version__ = "0.1.0"
