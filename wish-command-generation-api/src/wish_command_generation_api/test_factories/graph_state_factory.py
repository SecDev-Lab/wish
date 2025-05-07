"""Factory for GraphState model."""

import factory
from factory.faker import Faker
from wish_models.command_result import CommandResult
from wish_models.test_factories.command_input_factory import CommandInputFactory
from wish_models.test_factories.command_result_network_error_factory import CommandResultNetworkErrorFactory
from wish_models.test_factories.command_result_timeout_factory import CommandResultTimeoutFactory

from wish_command_generation_api.models import GeneratedCommand, GraphState


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

    @classmethod
    def create_with_timeout_error(
        cls, query: str, command: str, timeout_sec: int = 60, context: dict = None
    ) -> GraphState:
        """タイムアウトエラー状態のGraphStateを作成する

        Args:
            query: ユーザークエリ
            command: タイムアウトしたコマンド
            timeout_sec: タイムアウト値（秒）
            context: コンテキスト情報（省略可）

        Returns:
            GraphState: タイムアウトエラー状態のGraphState
        """
        timeout_result = CommandResultTimeoutFactory.create_with_command(command, timeout_sec)
        return cls(
            query=query,
            context=context or {},
            failed_command_results=[timeout_result],
            error_type="TIMEOUT",
            is_retry=True
        )

    @classmethod
    def create_with_network_error(
        cls, query: str, command: str, timeout_sec: int = 60,
        log_summary: str = None, context: dict = None
    ) -> GraphState:
        """ネットワークエラー状態のGraphStateを作成する

        Args:
            query: ユーザークエリ
            command: ネットワークエラーが発生したコマンド
            timeout_sec: タイムアウト値（秒）
            log_summary: エラーログの要約（省略可）
            context: コンテキスト情報（省略可）

        Returns:
            GraphState: ネットワークエラー状態のGraphState
        """
        network_error_result = CommandResultNetworkErrorFactory.create_with_command(
            command, timeout_sec, log_summary
        )
        return cls(
            query=query,
            context=context or {},
            failed_command_results=[network_error_result],
            error_type="NETWORK_ERROR",
            is_retry=True
        )
