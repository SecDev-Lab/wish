"""Factory for GenerateResponse model."""

import factory

from wish_command_generation_api.models import GenerateResponse
from wish_command_generation_api.test_factories.generated_command_factory import GeneratedCommandFactory


class GenerateResponseFactory(factory.Factory):
    """Factory for creating GenerateResponse objects for testing."""

    class Meta:
        model = GenerateResponse

    generated_commands = factory.List([
        factory.SubFactory(GeneratedCommandFactory)
    ])
    error = None

    @classmethod
    def create_with_commands(cls, commands: list[tuple[str, str]]) -> GenerateResponse:
        """Create a GenerateResponse with specific commands.

        Args:
            commands: List of tuples (command, explanation)
        """
        generated_commands = [
            GeneratedCommandFactory.create_with_command(cmd, explanation)
            for cmd, explanation in commands
        ]
        return cls(generated_commands=generated_commands)

    @classmethod
    def create_with_error(cls, error_message: str) -> GenerateResponse:
        """Create a GenerateResponse with an error message."""
        return cls(generated_commands=[], error=error_message)

    @classmethod
    def create_empty(cls) -> GenerateResponse:
        """Create an empty GenerateResponse with no commands."""
        return cls(generated_commands=[])
