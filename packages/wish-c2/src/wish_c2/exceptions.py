"""C2-specific exceptions."""


class C2Error(Exception):
    """Base exception for C2 operations."""

    pass


class ConnectionError(C2Error):
    """Connection error to C2 server."""

    pass


class SessionNotFoundError(C2Error):
    """Session not found error."""

    pass


class SecurityError(C2Error):
    """Security violation error."""

    pass


class CommandExecutionError(C2Error):
    """Command execution error."""

    pass


class AuthenticationError(C2Error):
    """Authentication error."""

    pass


class ConfigurationError(C2Error):
    """Configuration error."""

    pass
