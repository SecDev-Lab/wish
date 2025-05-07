"""Factory for creating SliverBackend instances for testing."""

import factory
from unittest.mock import AsyncMock, MagicMock

from wish_command_execution.backend.sliver import SliverBackend


class SliverBackendFactory(factory.Factory):
    """Factory for creating SliverBackend instances."""

    class Meta:
        model = SliverBackend

    session_id = factory.Faker("uuid4")
    client_config_path = factory.Faker("file_path", extension="json")

    @classmethod
    def create_with_mocks(cls, **kwargs):
        """Create a SliverBackend with mocked client and session.

        Args:
            **kwargs: Additional attributes to set on the backend.

        Returns:
            SliverBackend: A configured SliverBackend instance with mocks.
        """
        backend = cls.create(**kwargs)
        
        # Create mock client
        mock_client = MagicMock()
        mock_client.connect = AsyncMock()
        
        # Create mock interactive session
        mock_session = MagicMock()
        mock_session.os = "Linux"
        mock_session.arch = "x86_64"
        mock_session.version = "5.10.0"
        mock_session.hostname = "test-host"
        mock_session.username = "test-user"
        mock_session.uid = "1000"
        mock_session.gid = "1000"
        mock_session.pid = 12345
        mock_session.execute = AsyncMock()
        mock_session.is_dead = False
        
        # Configure client to return session
        mock_client.interact_session = AsyncMock(return_value=mock_session)
        
        # Set mocks on backend
        backend.client = mock_client
        backend.interactive_session = mock_session
        
        return backend
