"""Tests for the result combiner node."""

import os
import tempfile
from unittest.mock import patch

import pytest
from wish_models.command_result import LogFiles, CommandResult
from wish_models.command_result.command_state import CommandState

from wish_log_analysis.models import GraphState
from wish_log_analysis.nodes.result_combiner import combine_results


class TestResultCombiner:
    """Tests for the result combiner node."""

    def test_combine_results(self):
        """Test that the result combiner node works correctly."""
        # Create temporary log files
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
            stdout_file.write("Hello, World!")
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
            stderr_file.write("")

        try:
            # Create a mock command result using the factory method
            log_files = LogFiles(
                stdout=stdout_file.name,
                stderr=stderr_file.name,
            )
            command_result = CommandResult.create(
                num=1,
                command="echo 'Hello, World!'",
                log_files=log_files,
            )
            command_result.exit_code = 0

            # Create a mock graph state
            state = GraphState(
                command_result=command_result,
                log_summary="Hello, World!",
                command_state=CommandState.SUCCESS,
            )

            # Call the function
            result = combine_results(state)

            # Check that the result is correct
            assert result.analyzed_command_result is not None
            assert result.analyzed_command_result.command == "echo 'Hello, World!'"
            assert result.analyzed_command_result.exit_code == 0
            assert result.analyzed_command_result.log_files == command_result.log_files
            assert result.analyzed_command_result.log_summary == "Hello, World!"
            assert result.analyzed_command_result.state == CommandState.SUCCESS
        finally:
            # Clean up the temporary files
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)

    def test_combine_results_missing_fields(self):
        """Test that the result combiner node raises an error if fields are missing."""
        # Create a mock command result using the factory method
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
            stdout_file.write("")
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
            stderr_file.write("")

        try:
            log_files = LogFiles(
                stdout=stdout_file.name,
                stderr=stderr_file.name,
            )
            command_result = CommandResult.create(
                num=1,
                command="echo 'Hello, World!'",
                log_files=log_files,
            )
            command_result.exit_code = 0

            # Create a mock graph state with missing log_summary
            state1 = GraphState(
                command_result=command_result,
                command_state=CommandState.SUCCESS,
            )

            # Create a mock graph state with missing command_state
            state2 = GraphState(
                command_result=command_result,
                log_summary="Hello, World!",
            )

            # Check that the function raises an error
            with pytest.raises(ValueError):
                combine_results(state1)

            with pytest.raises(ValueError):
                combine_results(state2)
        finally:
            # Clean up the temporary files
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)
