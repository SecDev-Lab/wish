"""Exceptions for the command generation client."""


class CommandGenerationError(Exception):
    """Exception raised when command generation fails."""

    def __init__(self, message: str, api_response: str = None):
        """Initialize the exception.

        Args:
            message: The error message.
            api_response: The API response that caused the error (if available).
        """
        self.message = message
        self.api_response = api_response
        super().__init__(self.message)
