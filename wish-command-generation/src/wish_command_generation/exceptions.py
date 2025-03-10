"""Exceptions for wish-command-generation."""


class CommandGenerationError(Exception):
    """Exception raised for errors during command generation."""

    def __init__(self, message: str, api_response: str = None):
        """Initialize the exception.
        Args:
            message: Error message
            api_response: The raw API response that caused the error (if available)
        """
        super().__init__(message)
        self.message = message
        self.api_response = api_response

    def __str__(self) -> str:
        """Return string representation of the error."""
        return self.message
