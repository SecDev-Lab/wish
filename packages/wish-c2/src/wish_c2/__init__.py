"""wish-c2: C2 framework connectors for wish"""

from .base import BaseC2Connector
from .exceptions import (
    AuthenticationError,
    C2Error,
    CommandExecutionError,
    ConfigurationError,
    ConnectionError,
    SecurityError,
    SessionNotFoundError,
)
from .factory import create_c2_connector, get_c2_connector_from_config
from .models import (
    C2Config,
    CommandResult,
    FileTransferProgress,
    ImplantConfig,
    ImplantInfo,
    InteractiveShell,
    Session,
    SessionStatus,
    StagerListener,
    StagingServer,
)

__version__ = "0.1.0"

__all__ = [
    # Base classes
    "BaseC2Connector",
    # Factory
    "create_c2_connector",
    "get_c2_connector_from_config",
    # Models
    "Session",
    "SessionStatus",
    "InteractiveShell",
    "C2Config",
    "CommandResult",
    "FileTransferProgress",
    "ImplantConfig",
    "ImplantInfo",
    "StagerListener",
    "StagingServer",
    # Exceptions
    "C2Error",
    "ConnectionError",
    "SessionNotFoundError",
    "SecurityError",
    "CommandExecutionError",
    "AuthenticationError",
    "ConfigurationError",
]
