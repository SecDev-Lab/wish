"""Factory for creating log directory creator functions for testing."""

from pathlib import Path
from unittest.mock import MagicMock


class LogDirCreatorFactory:
    """Factory for creating log directory creator functions."""

    @staticmethod
    def create(base_path="/mock/log/dir"):
        """Create a log directory creator function.

        Args:
            base_path: Base path for log directories.

        Returns:
            function: A function that creates log directories.
        """
        def log_dir_creator(wish_id):
            """Create a log directory for a wish.

            Args:
                wish_id: The ID of the wish.

            Returns:
                Path: The path to the log directory.
            """
            return Path(f"{base_path}/{wish_id}")
        
        return log_dir_creator

    @staticmethod
    def create_mock():
        """Create a mock log directory creator function.

        Returns:
            MagicMock: A mock function that returns a Path.
        """
        mock_creator = MagicMock()
        mock_creator.return_value = Path("/mock/log/dir")
        return mock_creator
