"""Factory for creating CommandExecutor instances for testing."""

from unittest.mock import AsyncMock

import factory

from wish_command_execution.command_executor import CommandExecutor
from wish_command_execution.test_factories.bash_backend_factory import BashBackendFactory
from wish_command_execution.test_factories.log_dir_creator_factory import LogDirCreatorFactory


class CommandExecutorFactory(factory.Factory):
    """Factory for creating CommandExecutor instances."""

    class Meta:
        model = CommandExecutor

    backend = factory.SubFactory(BashBackendFactory)
    log_dir_creator = factory.LazyFunction(LogDirCreatorFactory.create_mock)
    run_id = factory.Faker("uuid4")

    @classmethod
    def create_with_mocks(cls, **kwargs):
        """Create a CommandExecutor with mocked methods.

        Args:
            **kwargs: Additional attributes to set on the executor.

        Returns:
            CommandExecutor: A configured CommandExecutor instance with mocks.
        """
        executor = cls.create(**kwargs)

        # Mock methods
        executor.execute_command = AsyncMock()
        executor.check_running_commands = AsyncMock()
        executor.cancel_command = AsyncMock(return_value="Command cancelled")

        return executor
