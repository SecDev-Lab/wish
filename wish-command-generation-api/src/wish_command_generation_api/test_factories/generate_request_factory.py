"""Factory for GenerateRequest model."""

import factory
from factory.faker import Faker
from wish_models.command_result import CommandResult
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory

from wish_command_generation_api.models import GenerateRequest


class GenerateRequestFactory(factory.Factory):
    """Factory for creating GenerateRequest objects for testing."""

    class Meta:
        model = GenerateRequest

    query = Faker("sentence")
    context = factory.Dict({
        "current_directory": "/home/user",
        "history": factory.List([
            "cd /home/user",
            "mkdir test"
        ]),
        "initial_timeout_sec": 60
    })
    failed_command_results = None
    run_id = factory.Sequence(lambda n: f"run-{n}")

    @classmethod
    def create_with_query(cls, query: str) -> GenerateRequest:
        """Create a GenerateRequest with a specific query."""
        return cls(query=query)

    @classmethod
    def create_with_context(cls, query: str, context: dict) -> GenerateRequest:
        """Create a GenerateRequest with a specific query and context."""
        return cls(query=query, context=context)

    @classmethod
    def create_with_failed_commands(cls, query: str, failed_commands: list[CommandResult]) -> GenerateRequest:
        """Create a GenerateRequest with a specific query and failed command results."""
        return cls(query=query, failed_command_results=failed_commands)

    @classmethod
    def create_with_single_failed_command(cls, query: str, command: str, exit_code: int = 1) -> GenerateRequest:
        """Create a GenerateRequest with a specific query and a single failed command."""
        failed_command = CommandResultSuccessFactory(command=command, exit_code=exit_code)
        return cls(query=query, failed_command_results=[failed_command])
