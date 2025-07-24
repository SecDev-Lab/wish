"""Configuration management for Sliver C2 integration."""

import logging
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class SliverSafetyConfig(BaseModel):
    """Safety configuration for Sliver connector."""

    sandbox_mode: bool = Field(default=True, description="Enable sandbox restrictions")
    read_only: bool = Field(default=False, description="Prevent write operations")
    allowed_commands: list[str] = Field(
        default_factory=lambda: ["ls", "pwd", "whoami", "id", "cat", "ps", "netstat", "ifconfig", "uname", "env"],
        description="Whitelist of allowed commands",
    )
    blocked_paths: list[str] = Field(
        default_factory=lambda: ["/etc/shadow", "/etc/passwd", "/root/.ssh"],
        description="Paths to block access",
    )
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size for operations")


class SliverConfig(BaseModel):
    """Configuration for Sliver C2 connector."""

    mode: str = Field(default="mock", description="Connector mode: mock, real, or safe")
    enabled: bool = Field(default=True, description="Whether Sliver C2 is enabled")
    config_path: str | None = Field(default=None, description="Path to Sliver client config file")
    server: str | None = Field(default=None, description="Override server address")
    demo_mode: bool = Field(default=True, description="Enable demo mode for mock connector")
    safety: SliverSafetyConfig = Field(default_factory=SliverSafetyConfig, description="Safety configuration")

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate connector mode."""
        valid_modes = ["mock", "real", "safe"]
        if v not in valid_modes:
            raise ValueError(f"Invalid mode '{v}'. Must be one of: {valid_modes}")
        return v

    @field_validator("config_path")
    @classmethod
    def validate_config_path(cls, v: str | None) -> str | None:
        """Validate and expand config path."""
        if v is None:
            return None

        # Expand user and environment variables
        path = Path(os.path.expanduser(os.path.expandvars(v)))

        # For real/safe modes, path must exist
        # But during validation, we just expand the path
        return str(path)


class C2Configuration(BaseModel):
    """Overall C2 configuration."""

    sliver: SliverConfig = Field(default_factory=SliverConfig, description="Sliver C2 configuration")


def load_sliver_config_from_env() -> SliverConfig:
    """Load Sliver configuration from environment variables.

    Environment variables:
        WISH_C2_MODE: Connector mode (mock/real/safe)
        WISH_C2_SLIVER_CONFIG: Path to Sliver config file
        WISH_C2_SLIVER_SERVER: Override server address
        WISH_C2_SANDBOX: Enable sandbox mode (true/false)
        WISH_C2_READONLY: Enable read-only mode (true/false)

    Returns:
        SliverConfig instance
    """
    config = SliverConfig()

    # Mode
    if mode := os.getenv("WISH_C2_MODE"):
        config.mode = mode

    # Config path
    if config_path := os.getenv("WISH_C2_SLIVER_CONFIG"):
        config.config_path = config_path

    # Server override
    if server := os.getenv("WISH_C2_SLIVER_SERVER"):
        config.server = server

    # Safety settings
    if sandbox := os.getenv("WISH_C2_SANDBOX"):
        config.safety.sandbox_mode = sandbox.lower() in ["true", "1", "yes", "on"]

    if readonly := os.getenv("WISH_C2_READONLY"):
        config.safety.read_only = readonly.lower() in ["true", "1", "yes", "on"]

    logger.debug(f"Loaded Sliver config from environment: mode={config.mode}")
    return config


def merge_configs(base: SliverConfig, override: dict[str, Any]) -> SliverConfig:
    """Merge configuration with overrides.

    Args:
        base: Base configuration
        override: Dictionary of overrides

    Returns:
        Merged configuration
    """
    # Convert to dict, merge, and recreate
    base_dict = base.model_dump()

    # Deep merge for nested configs
    if "safety" in override and isinstance(override["safety"], dict):
        base_dict["safety"].update(override["safety"])
        override = override.copy()
        del override["safety"]

    base_dict.update(override)
    return SliverConfig(**base_dict)


def get_default_config_path() -> Path:
    """Get default Sliver config path.

    Returns:
        Default config path (~/.sliver-client/configs/default.cfg)
    """
    return Path.home() / ".sliver-client" / "configs" / "default.cfg"


def validate_sliver_config_file(config_path: Path) -> bool:
    """Validate Sliver configuration file.

    Args:
        config_path: Path to config file

    Returns:
        True if valid

    Raises:
        ConfigurationError: If config is invalid
    """
    from ..exceptions import ConfigurationError

    if not config_path.exists():
        raise ConfigurationError(f"Config file not found: {config_path}")

    if not config_path.is_file():
        raise ConfigurationError(f"Config path is not a file: {config_path}")

    # Check permissions (should not be world-readable)
    stat = config_path.stat()
    if stat.st_mode & 0o077:
        logger.warning(f"Config file has overly permissive permissions: {oct(stat.st_mode)}")

    # Try to read file
    try:
        config_path.read_text()
    except PermissionError as e:
        raise ConfigurationError(f"Permission denied reading config: {config_path}") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to read config file: {e}") from e

    return True
