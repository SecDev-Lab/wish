"""Tests for the logging module."""

import logging
import os
import pytest
from unittest.mock import patch

from wish_sh.logging import setup_logger


class TestLogging:
    """Tests for the logging module."""

    def test_setup_logger_returns_logger(self):
        """Test that setup_logger returns a logger instance."""
        logger = setup_logger("test_logger")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_logger"

    def test_setup_logger_level_from_parameter(self):
        """Test that the logger level is set correctly from the parameter."""
        logger = setup_logger("test_logger_param", "DEBUG")
        assert logger.level == logging.DEBUG

    @patch.dict(os.environ, {"WISH_LOG_LEVEL": "ERROR"})
    def test_setup_logger_level_from_env_var(self):
        """Test that the logger level is set correctly from the environment variable."""
        logger = setup_logger("test_logger_env")
        assert logger.level == logging.ERROR

    @patch.dict(os.environ, {}, clear=True)
    def test_setup_logger_default_level(self):
        """Test that the logger level defaults to INFO."""
        logger = setup_logger("test_logger_default")
        assert logger.level == logging.INFO

    def test_setup_logger_adds_handler_once(self):
        """Test that a handler is added only if the logger doesn't already have handlers."""
        logger_name = "test_logger_handlers"
        logger1 = setup_logger(logger_name)
        initial_handler_count = len(logger1.handlers)
        assert initial_handler_count > 0

        # Call setup_logger again with the same name
        logger2 = setup_logger(logger_name)
        # Should be the same logger instance
        assert logger1 is logger2
        # Handler count should not change
        assert len(logger2.handlers) == initial_handler_count

    def test_setup_logger_invalid_level(self):
        """Test that an invalid log level defaults to INFO."""
        logger = setup_logger("test_logger_invalid", "INVALID_LEVEL")
        assert logger.level == logging.INFO
