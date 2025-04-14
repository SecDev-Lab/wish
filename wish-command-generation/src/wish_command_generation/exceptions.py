"""Exceptions for the command generation client."""


class CommandGenerationError(Exception):
    """Exception raised when command generation fails."""

    def __init__(self, message: str):
        """Initialize the exception.

        Args:
            message: The error message.
        """
        self.message = message
        super().__init__(self.message)
