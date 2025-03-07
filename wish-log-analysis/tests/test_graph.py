"""Tests for the log analysis graph."""

import os
import tempfile
from unittest.mock import patch

import pytest
from wish_models.command_result import LogFiles, CommandResult
from wish_models.command_result.command_state import CommandState

from wish_log_analysis.graph import create_log_analysis_graph
from wish_log_analysis.models import GraphState


class TestGraph:
    """Tests for the log analysis graph."""

    @patch("wish_log_analysis.nodes.log_summarization.summarize_log")
    @patch("wish_log_analysis.nodes.command_state_classifier.classify_command_state")
    @patch("wish_log_analysis.nodes.result_combiner.combine_results")
    def test_graph_execution(self, mock_combine_results, mock_classify_command_state, mock_summarize_log):
        """Test that the graph executes in the correct order."""
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

            # Set up the mocks
            mock_summarize_log.return_value = GraphState(
                command_result=command_result,
                log_summary="Hello, World!",
            )
            mock_classify_command_state.return_value = GraphState(
                command_result=command_result,
                command_state=CommandState.SUCCESS,
            )
            mock_combine_results.return_value = GraphState(
                command_result=command_result,
                log_summary="Hello, World!",
                command_state=CommandState.SUCCESS,
                analyzed_command_result=CommandResult(
                    num=1,
                    command="echo 'Hello, World!'",
                    exit_code=0,
                    log_files=log_files,
                    log_summary="Hello, World!",
                    state=CommandState.SUCCESS,
                    created_at=command_result.created_at,
                ),
            )

            # Create the graph
            graph = create_log_analysis_graph()

            # Execute the graph
            result = graph.invoke({"command_result": command_result})

            # Check that the mocks were called
            mock_summarize_log.assert_called_once()
            mock_classify_command_state.assert_called_once()
            mock_combine_results.assert_called_once()

            # Check that the result is correct
            assert result["analyzed_command_result"] is not None
            assert result["analyzed_command_result"].summary == "Hello, World!"
            assert result["analyzed_command_result"].state == CommandState.SUCCESS
        finally:
            # Clean up the temporary files
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)
