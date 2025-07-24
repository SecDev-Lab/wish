"""
Configuration management for wish.

This module provides the core configuration management functionality,
including reading from ~/.wish/config.toml and environment variables.
"""

import logging
import os
from pathlib import Path
from typing import Any

import tomli as tomllib
import tomli_w
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class LLMConfig(BaseModel):
    """LLM configuration section."""

    provider: str = "openai"
    model: str = "gpt-4o"
    api_key: str = ""
    timeout: int = 120
    max_tokens: int = 8000
    temperature: float = 0.1


class GeneralConfig(BaseModel):
    """General configuration section."""

    default_mode: str = "recon"
    auto_save_interval: int = 30
    max_session_history: int = 10
    debug_mode: bool = False


class C2Config(BaseModel):
    """C2 configuration section."""

    sliver_host: str = "127.0.0.1"
    sliver_port: int = 31337
    sliver_cert_path: str = "~/.sliver/configs/default.crt"


class WishConfig(BaseModel):
    """Main configuration model for wish."""

    general: GeneralConfig = Field(default_factory=GeneralConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    c2: C2Config = Field(default_factory=C2Config)


class ConfigManager:
    """Configuration manager for wish platform."""

    def __init__(self, config_path: str | None = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file (defaults to ~/.wish/config.toml)
        """
        self.config_path = Path(config_path or "~/.wish/config.toml").expanduser()
        self._config: WishConfig | None = None
        self._ensure_config_dir()

    def _ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Set appropriate permissions for ~/.wish directory
        if os.name == "posix":  # Unix-like systems
            os.chmod(self.config_path.parent, 0o700)

    def load_config(self) -> WishConfig:
        """Load configuration from file and environment variables.

        Returns:
            WishConfig object with loaded configuration
        """
        if self._config is not None:
            return self._config

        # Start with default configuration
        config_data = {}

        # Load from file if it exists
        if self.config_path.exists():
            try:
                with open(self.config_path, "rb") as f:
                    config_data = tomllib.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_path}: {e}")
                config_data = {}
        else:
            logger.info(f"Config file {self.config_path} not found, using defaults")

        # Apply environment variable overrides
        config_data = self._apply_env_overrides(config_data)

        # Create and cache configuration
        self._config = WishConfig(**config_data)
        return self._config

    def _apply_env_overrides(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variable overrides to configuration.

        Args:
            config_data: Base configuration data

        Returns:
            Configuration data with environment overrides applied
        """
        # Ensure nested dictionaries exist
        if "llm" not in config_data:
            config_data["llm"] = {}
        if "general" not in config_data:
            config_data["general"] = {}
        if "c2" not in config_data:
            config_data["c2"] = {}

        # LLM configuration overrides
        if openai_key := os.getenv("OPENAI_API_KEY"):
            config_data["llm"]["api_key"] = openai_key
            logger.debug("Using OPENAI_API_KEY from environment")

        if llm_timeout := os.getenv("WISH_LLM_TIMEOUT"):
            try:
                config_data["llm"]["timeout"] = int(llm_timeout)
                logger.debug(f"Using WISH_LLM_TIMEOUT from environment: {llm_timeout}s")
            except ValueError:
                logger.warning(f"Invalid WISH_LLM_TIMEOUT value: {llm_timeout}, using default")

        # General configuration overrides
        if debug_mode := os.getenv("WISH_DEBUG"):
            config_data["general"]["debug_mode"] = debug_mode.lower() in ("true", "1", "yes")

        return config_data

    def save_config(self, config: WishConfig | None = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save (uses current config if None)
        """
        if config is None:
            config = self._config or WishConfig()

        try:
            # Convert to dict and remove empty api_key for security
            config_dict = config.model_dump()
            if config_dict.get("llm", {}).get("api_key") == "":
                config_dict["llm"]["api_key"] = ""

            # Write to file
            with open(self.config_path, "wb") as f:
                tomli_w.dump(config_dict, f)

            # Set appropriate permissions
            if os.name == "posix":
                os.chmod(self.config_path, 0o600)

            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Failed to save config to {self.config_path}: {e}")
            raise

    def get_llm_config(self) -> LLMConfig:
        """Get LLM configuration.

        Returns:
            LLM configuration object
        """
        return self.load_config().llm

    def get_general_config(self) -> GeneralConfig:
        """Get general configuration.

        Returns:
            General configuration object
        """
        return self.load_config().general

    def get_c2_config(self) -> C2Config:
        """Get C2 configuration.

        Returns:
            C2 configuration object
        """
        return self.load_config().c2

    def initialize_config(self, force: bool = False) -> None:
        """Initialize configuration file with defaults.

        Args:
            force: Whether to overwrite existing config file
        """
        if self.config_path.exists() and not force:
            logger.info(f"Config file {self.config_path} already exists")
            return

        # Create default configuration
        default_config = WishConfig()
        self.save_config(default_config)

        logger.info(f"Initialized config file at {self.config_path}")

    def set_api_key(self, api_key: str) -> None:
        """Set OpenAI API key in configuration.

        Args:
            api_key: OpenAI API key to set
        """
        config = self.load_config()
        config.llm.api_key = api_key
        self.save_config(config)

        # Update cached config
        self._config = config

        logger.info("OpenAI API key updated in configuration")

    def get_api_key(self) -> str | None:
        """Get OpenAI API key from configuration hierarchy.

        Follows fail-fast principle: returns None when no API key is configured,
        allowing calling code to immediately raise appropriate exceptions.

        Priority order:
        1. OPENAI_API_KEY environment variable (highest priority)
        2. Configuration file ~/.wish/config.toml [llm.api_key]
        3. None (triggers fail-fast behavior in calling code)

        Returns:
            API key if found, None otherwise (triggers fail-fast)
        """
        # Check environment variable first (highest priority)
        if api_key := os.getenv("OPENAI_API_KEY"):
            return api_key

        # Check configuration file
        config = self.load_config()
        if config.llm.api_key:
            return config.llm.api_key

        return None

    def validate_setup(self) -> dict[str, Any]:
        """Validate configuration setup.

        Returns:
            Dictionary with validation results
        """
        issues: list[str] = []
        result: dict[str, Any] = {
            "config_file_exists": self.config_path.exists(),
            "config_file_readable": False,
            "api_key_configured": False,
            "api_key_source": None,
            "issues": issues,
        }

        # Check config file
        if result["config_file_exists"]:
            try:
                self.load_config()
                result["config_file_readable"] = True
            except Exception as e:
                issues.append(f"Config file unreadable: {e}")

        # Check API key
        api_key = self.get_api_key()
        if api_key:
            result["api_key_configured"] = True
            if os.getenv("OPENAI_API_KEY"):
                result["api_key_source"] = "environment"
            else:
                result["api_key_source"] = "config_file"
        else:
            issues.append("No OpenAI API key configured")

        return result


# Global configuration manager instance
_config_manager: ConfigManager | None = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance.

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_api_key() -> str | None:
    """Convenience function to get OpenAI API key.

    Returns:
        API key if configured, None otherwise
    """
    return get_config_manager().get_api_key()


def get_llm_config() -> LLMConfig:
    """Convenience function to get LLM configuration.

    Returns:
        LLM configuration object
    """
    return get_config_manager().get_llm_config()
