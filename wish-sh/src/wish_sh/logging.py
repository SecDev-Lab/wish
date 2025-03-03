"""Logging utilities for wish-sh."""

import logging
import os
import sys


def setup_logger(name: str, level: str | None = None) -> logging.Logger:
    """Set up a logger with the specified name and level.
    
    Args:
        name: The name of the logger.
        level: The logging level. If None, uses the WISH_LOG_LEVEL environment variable
               or defaults to INFO.
               
    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Get log level from environment variable or parameter, default to WARNING
    if level is None:
        level = os.environ.get("WISH_LOG_LEVEL", "INFO").upper()
    
    # Set the log level
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Only add handler if not already added to avoid duplicate handlers
    if not logger.handlers:
        # Set up console handler with a formatter
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger
