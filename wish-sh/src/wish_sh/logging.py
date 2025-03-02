"""Logging utilities for wish-sh."""

import logging
import os
from typing import Optional


def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Set up a logger with the specified name and level.
    
    Args:
        name: The name of the logger.
        level: The logging level. If None, uses the WISH_LOG_LEVEL environment variable
               or defaults to INFO.
               
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Get log level from environment variable or parameter, default to INFO
    if level is None:
        level = os.environ.get("WISH_LOG_LEVEL", "INFO").upper()
    
    # Set the log level
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Only add handler if not already added to avoid duplicate handlers
    if not logger.handlers:
        # Set up console handler with a formatter
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
