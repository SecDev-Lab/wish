"""Factory for GraphState model."""

import factory
from factory.faker import Faker
from wish_models.command_result import CommandInput, CommandResult
from wish_models.test_factories.command_input_factory import CommandInputFactory
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory

from wish_command_generation_api.models import GraphState, GeneratedCommand


class GraphStateFactory(factory.Factory):
    """Factory for creating GraphState objects for testing."""

    class Meta:
        model = GraphState

    query = Faker("sentence")
    context = factory.Dict({
        "current_directory": "/home/user",
        "history": factory.List([
            "cd /home/user",
            "mkdir test"
        ]),
        "initial_timeout_sec": 60
    })
    run_id = factory.Sequence(lambda n: f"run-{n}")
    processed_query = None
    command_candidates = None
    generated_commands = None
    api_error = False
    failed_command_results = None
    is_retry = False
    error_type = None

    @classmethod
    def create_with_processed_query(cls, query: str, processed_query: str) -> GraphState:
        """Create a GraphState with a specific query and processed query."""
        return cls(query=query, processed_query=processed_query)

    @classmethod
    def create_with_command_candidates(cls, query: str, commands: list[str]) -> GraphState:
        """Create a GraphState with a specific query and command candidates."""
        command_inputs = [CommandInputFactory(command=cmd, timeout_sec=60) for cmd in commands]
        return cls(query=query, command_candidates=command_inputs)

    @classmethod
    def create_with_generated_commands(cls, query: str, commands: list[tuple[str, str]]) -> GraphState:
        """Create a GraphState with a specific query and generated commands.
        
        Args:
            query: The user query
            commands: List of tuples (command, explanation)
        """
        generated_commands = []
        for cmd, explanation in commands:
            command_input = CommandInputFactory(command=cmd, timeout_sec=60)
            generated_commands.append(
                GeneratedCommand(command_input=command_input, explanation=explanation)
            )
        return cls(query=query, generated_commands=generated_commands)

    @classmethod
    def create_with_error(cls, query: str, error_type: str) -> GraphState:
        """Create a GraphState with a specific query and error type."""
        return cls(query=query, is_retry=True, error_type=error_type)

    @classmethod
    def create_with_feedback(cls, query: str, failed_commands: list[CommandResult]) -> GraphState:
        """Create a GraphState with a specific query and failed command results."""
        return cls(query=query, failed_command_results=failed_commands)
