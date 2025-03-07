"""Logging utilities for the knowledge loader package."""

import logging
from typing import Optional


def setup_logger(
    name: str = "wish-knowledge-loader",
    level: int = logging.INFO,
    log_format: Optional[str] = None,
) -> logging.Logger:
    """Set up a logger with the specified name and level.

    Args:
        name: Logger name
        level: Logging level
        log_format: Log format string

    Returns:
        Configured logger
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure root logger
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,  # Override any existing configuration
    )

    # Get logger for the specified name
    logger = logging.getLogger(name)
    logger.setLevel(level)

    return logger
