"""Tests for the LogAnalyzer class."""

from unittest.mock import patch

import pytest
from wish_models.command_result import LogFiles, CommandResult
from wish_models.command_result.command_state import CommandState

from wish_log_analysis.analyzer import LogAnalyzer


class TestLogAnalyzer:
    """Tests for the LogAnalyzer class."""

    @patch("wish_log_analysis.graph.create_log_analysis_graph")
    def test_analyze_result(self, mock_create_graph):
        """Test that the analyze_result method works correctly."""
        # Create temporary log files
        import tempfile
        import os
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

            # Create a mock analyzed command result
            analyzed_command_result = CommandResult(
                num=1,
                command="echo 'Hello, World!'",
                exit_code=0,
                log_files=log_files,
                log_summary="Hello, World!",
                state=CommandState.SUCCESS,
                created_at=command_result.created_at,
            )

            # Set up the mock
            mock_graph = mock_create_graph.return_value
            mock_graph.invoke.return_value = {
                "analyzed_command_result": analyzed_command_result
            }

            # Create the analyzer
            analyzer = LogAnalyzer()

            # Call the method
            result = analyzer.analyze_result(command_result)

            # Check that the mock was called
            mock_create_graph.assert_called_once()
            mock_graph.invoke.assert_called_once_with({"command_result": command_result})

            # Check that the result is correct
            assert result == analyzed_command_result
        finally:
            # Clean up the temporary files
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)
