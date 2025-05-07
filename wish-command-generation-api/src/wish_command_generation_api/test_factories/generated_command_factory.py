"""Factory for GeneratedCommand model."""

import factory
from factory.faker import Faker
from wish_models.test_factories.command_input_factory import CommandInputFactory

from wish_command_generation_api.models import GeneratedCommand


class GeneratedCommandFactory(factory.Factory):
    """Factory for creating GeneratedCommand objects for testing."""

    class Meta:
        model = GeneratedCommand

    command_input = factory.SubFactory(CommandInputFactory)
    explanation = Faker("paragraph")

    @classmethod
    def create_with_command(cls, command: str, explanation: str | None = None) -> GeneratedCommand:
        """Create a GeneratedCommand with a specific command and explanation.
        
        Args:
            command: The command string
            explanation: Optional explanation, will use a random one if not provided
        """
        command_input = CommandInputFactory(command=command, timeout_sec=60)
        if explanation is None:
            return cls(command_input=command_input)
        return cls(command_input=command_input, explanation=explanation)

    @classmethod
    def create_with_timeout(cls, command: str, timeout_sec: int, explanation: str | None = None) -> GeneratedCommand:
        """Create a GeneratedCommand with a specific command, timeout and explanation.
        
        Args:
            command: The command string
            timeout_sec: The timeout in seconds
            explanation: Optional explanation, will use a random one if not provided
        """
        command_input = CommandInputFactory(command=command, timeout_sec=timeout_sec)
        if explanation is None:
            return cls(command_input=command_input)
        return cls(command_input=command_input, explanation=explanation)
