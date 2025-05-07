"""Factory for creating BashBackend instances for testing."""

import factory

from wish_command_execution.backend.bash import BashBackend


class BashBackendFactory(factory.Factory):
    """Factory for creating BashBackend instances."""

    class Meta:
        model = BashBackend

    run_id = factory.Faker("uuid4")

    @classmethod
    def create_with_running_commands(cls, running_commands=None):
        """Create a BashBackend with pre-configured running commands.

        Args:
            running_commands: Dictionary of running commands to set.

        Returns:
            BashBackend: A configured BashBackend instance.
        """
        backend = cls.create()
        if running_commands:
            backend.running_commands = running_commands
        return backend
