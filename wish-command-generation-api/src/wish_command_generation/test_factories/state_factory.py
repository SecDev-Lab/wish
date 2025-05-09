"""Factory classes for state objects used in tests."""

import factory
from factory.faker import Faker
from wish_models.command_result import CommandInput
from wish_models.system_info import SystemInfo
from wish_models.wish.wish import Wish
from wish_models.wish.wish_state import WishState

from wish_command_generation.models import GraphState


class WishFactory(factory.Factory):
    """Factory for creating Wish objects."""

    class Meta:
        model = Wish

    id = factory.Sequence(lambda n: f"{n:010d}")
    wish = Faker("sentence")
    state = WishState.DOING
    command_results = factory.List([])
    created_at = factory.LazyFunction(lambda: Wish.create("dummy").created_at)
    finished_at = None

    @classmethod
    def create_with_specific_wish(cls, wish_text: str) -> Wish:
        """Create a Wish with a specific wish text."""
        return Wish.create(wish=wish_text)


class CommandInputFactory(factory.Factory):
    """Factory for creating CommandInput objects."""

    class Meta:
        model = CommandInput

    command = Faker("sentence")
    timeout_sec = 60

    @classmethod
    def create_with_specific_command(cls, command: str) -> CommandInput:
        """Create a CommandInput with a specific command."""
        return CommandInput(command=command, timeout_sec=60)


class GraphStateFactory(factory.Factory):
    """Factory for creating GraphState objects."""

    class Meta:
        model = GraphState

    wish = factory.SubFactory(WishFactory)
    context = factory.Dict({
        "initial_timeout_sec": 60
    })
    query = None
    command_inputs = factory.List([])

    @classmethod
    def create_with_specific_wish(cls, wish_text: str) -> GraphState:
        """Create a GraphState with a specific wish text."""
        wish = WishFactory.create_with_specific_wish(wish_text)
        # Create a context dictionary with initial_timeout_sec
        context = {"initial_timeout_sec": 60}
        return GraphState(wish=wish, context=context)

    @classmethod
    def create_with_context(cls, wish_text: str, context_docs: list[str]) -> GraphState:
        """Create a GraphState with a specific wish text and context."""
        wish = WishFactory.create_with_specific_wish(wish_text)
        context = {
            "docs": context_docs,
            "initial_timeout_sec": 60
        }
        return GraphState(wish=wish, context=context)

    @classmethod
    def create_with_query(cls, wish_text: str, query: str) -> GraphState:
        """Create a GraphState with a specific wish text and query."""
        wish = WishFactory.create_with_specific_wish(wish_text)
        # Create a context dictionary with initial_timeout_sec
        context = {"initial_timeout_sec": 60}
        return GraphState(wish=wish, query=query, context=context)

    @classmethod
    def create_with_command_inputs(cls, wish_text: str, commands: list[str]) -> GraphState:
        """Create a GraphState with a specific wish text and command inputs."""
        wish = WishFactory.create_with_specific_wish(wish_text)
        command_inputs = [CommandInputFactory.create_with_specific_command(cmd) for cmd in commands]
        # Create a context dictionary with initial_timeout_sec
        context = {"initial_timeout_sec": 60}
        return GraphState(wish=wish, command_inputs=command_inputs, context=context)

    @classmethod
    def create_with_system_info(cls, wish_text: str, system_os: str = "Linux",
                               system_arch: str = "x86_64", system_version: str = "5.15.0") -> GraphState:
        """Create a GraphState with a specific wish text and system information."""
        wish = WishFactory.create_with_specific_wish(wish_text)
        system_info = SystemInfo(
            os=system_os,
            arch=system_arch,
            version=system_version,
            hostname="test-host",
            username="test-user",
        )
        # Create a context dictionary with initial_timeout_sec
        context = {"initial_timeout_sec": 60}
        return GraphState(wish=wish, system_info=system_info, context=context)
