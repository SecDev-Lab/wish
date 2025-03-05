"""Test factories for wish_sh."""

from wish_sh.test_factories.command_execution_screen_factory import CommandExecutionScreenFactory
from wish_sh.test_factories.command_suggestion_factory import CommandSuggestionFactory
from wish_sh.test_factories.wish_input_factory import WishInputFactory
from wish_sh.test_factories.wish_manager_factory import WishManagerFactory

__all__ = [
    "WishManagerFactory",
    "CommandExecutionScreenFactory",
    "CommandSuggestionFactory",
    "WishInputFactory",
]
