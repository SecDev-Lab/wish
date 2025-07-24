"""Factory for creating C2 connectors."""

import logging
from pathlib import Path
from typing import Literal

from .base import BaseC2Connector
from .exceptions import C2Error

logger = logging.getLogger(__name__)

C2Type = Literal["sliver"]
ConnectorMode = Literal["real", "safe"]


def create_c2_connector(
    c2_type: C2Type = "sliver",
    mode: ConnectorMode = "real",
    config: dict | None = None,
) -> BaseC2Connector:
    """Create a C2 connector instance.

    Args:
        c2_type: Type of C2 framework (currently only "sliver")
        mode: Connector mode - "real" for actual Sliver, "safe" for sandboxed
        config: Configuration dictionary with mode-specific settings

    Returns:
        C2 connector instance

    Raises:
        ValueError: If invalid c2_type or mode is specified
        C2Error: If connector creation fails
    """
    if c2_type != "sliver":
        raise ValueError(f"Unsupported C2 type: {c2_type}")

    if mode == "real":
        logger.info("Creating real Sliver connector")
        if not config or "config_path" not in config:
            raise ValueError("Real mode requires 'config_path' in config")

        # Import here to avoid dependency issues when sliver-py is not needed
        from .sliver.connector import RealSliverConnector

        config_path = Path(config["config_path"]).expanduser()
        if not config_path.exists():
            raise C2Error(f"Sliver config file not found: {config_path}")

        # Extract SSL options from config
        ssl_options = config.get("ssl_options", {})
        return RealSliverConnector(config_path, ssl_options)

    elif mode == "safe":
        logger.info("Creating safe Sliver connector")
        if not config or "config_path" not in config:
            raise ValueError("Safe mode requires 'config_path' in config")

        # Import here to avoid dependency issues
        from .sliver.safety import SafeSliverConnector

        config_path = Path(config["config_path"]).expanduser()
        if not config_path.exists():
            raise C2Error(f"Sliver config file not found: {config_path}")

        safety_config = config.get("safety", {})
        ssl_options = config.get("ssl_options", {})
        return SafeSliverConnector(config_path, safety_config, ssl_options)

    else:
        raise ValueError(f"Unknown connector mode: {mode}")


def get_c2_connector_from_config(config: dict) -> BaseC2Connector:
    """Create C2 connector from configuration dictionary.

    Args:
        config: Configuration with c2.sliver section

    Returns:
        C2 connector instance

    Example config:
        {
            "c2": {
                "sliver": {
                    "mode": "real",
                    "enabled": true,
                    "config_path": "~/.sliver-client/configs/default.cfg",
                    "safety": {
                        "sandbox_mode": true,
                        "allowed_commands": ["ls", "pwd", "whoami"]
                    }
                }
            }
        }
    """
    c2_config = config.get("c2", {})
    sliver_config = c2_config.get("sliver", {})

    if not sliver_config.get("enabled", False):
        raise C2Error("Sliver C2 is not enabled in configuration")

    mode = sliver_config.get("mode", "real")
    connector_config = {
        "config_path": sliver_config.get("config_path"),
        "demo_mode": sliver_config.get("demo_mode", True),
        "safety": sliver_config.get("safety", {}),
    }

    return create_c2_connector("sliver", mode=mode, config=connector_config)
