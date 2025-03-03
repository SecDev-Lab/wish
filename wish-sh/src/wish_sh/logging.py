"""Logging utilities for wish-sh."""

import logging
import os
import sys
from pathlib import Path


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
    
    # Get log level from environment variable or parameter, default to INFO
    if level is None:
        level = os.environ.get("WISH_LOG_LEVEL", "INFO").upper()
    
    # Set the log level
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Only add handler if not already added to avoid duplicate handlers
    if not logger.handlers:
        # Create logs directory if it doesn't exist
        log_dir = Path.home() / "wish_logs"
        log_dir.mkdir(exist_ok=True)
        
        # Set up file handler with a formatter
        log_file = log_dir / "wish.log"
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also log to console if requested
        if os.environ.get("WISH_CONSOLE_LOG", "FALSE").upper() == "TRUE":
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Log the location of the log file
        logger.info(f"Logging to {log_file}")
    
    return logger
