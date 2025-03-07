"""Tests for log_summarization.py."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result.log_files import LogFiles

from wish_log_analysis.nodes.log_summarization import summarize_log
from wish_log_analysis.test_factories import CommandResultFactory, GraphStateFactory


@pytest.fixture
def mock_chain():
    """Mock the chain used in summarize_log."""
    with patch("wish_log_analysis.nodes.log_summarization.PromptTemplate") as mock_prompt:
        with patch("wish_log_analysis.nodes.log_summarization.ChatOpenAI") as _:
            with patch("wish_log_analysis.nodes.log_summarization.StrOutputParser") as _:
                # Set up the mock chain
                mock_chain = MagicMock()
                mock_chain.invoke.return_value = "Mocked summary"

                # Create a mock for the pipe
                mock_pipe = MagicMock()
                mock_pipe.invoke.return_value = "Mocked summary"

                # Set up the mock prompt to return a mock pipe
                mock_prompt.from_template.return_value = MagicMock()
                mock_prompt.from_template.return_value.__or__.return_value = MagicMock()
                mock_prompt.from_template.return_value.__or__.return_value.__or__.return_value = mock_pipe

                yield mock_pipe


def test_summarize_log_with_log_files(mock_chain):
    """Test that summarize_log reads log files and generates a summary."""
    # Create temporary files for stdout and stderr
    stdout_content = "Hello, World!"
    stderr_content = "Error message"

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
        stdout_file.write(stdout_content)
        stdout_path = stdout_file.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
        stderr_file.write(stderr_content)
        stderr_path = stderr_file.name

    try:
        # Create a command result with log files
        log_files = LogFiles(stdout=stdout_path, stderr=stderr_path)
        command_result = CommandResultFactory(
            command="echo 'Hello, World!'",
            exit_code=0,
            log_files=log_files
        )

        # Create a graph state
        graph_state = GraphStateFactory.create_with_command_result(command_result)

        # Summarize the log
        result = summarize_log(graph_state)

        # Check that the log was summarized correctly
        assert result.log_summary == "Mocked summary"

        # Check that the chain was invoked with the correct arguments
        mock_chain.invoke.assert_called_once()
        args = mock_chain.invoke.call_args[0][0]
        assert args["command"] == "echo 'Hello, World!'"
        assert args["exit_code"] == 0
        assert args["stdout"] == stdout_content
        assert args["stderr"] == stderr_content

    finally:
        # Clean up the temporary files
        os.unlink(stdout_path)
        os.unlink(stderr_path)


def test_summarize_log_without_log_files(mock_chain):
    """Test that summarize_log handles missing log files."""
    # Create a command result without log files
    command_result = CommandResultFactory(
        command="echo 'Hello, World!'",
        exit_code=0,
        log_files=None
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Summarize the log
    result = summarize_log(graph_state)

    # Check that the log was summarized correctly
    assert result.log_summary == "Mocked summary"

    # Check that the chain was invoked with the correct arguments
    mock_chain.invoke.assert_called_once()
    args = mock_chain.invoke.call_args[0][0]
    assert args["command"] == "echo 'Hello, World!'"
    assert args["exit_code"] == 0
    assert args["stdout"] == ""
    assert args["stderr"] == ""


def test_summarize_log_with_nonexistent_log_files(mock_chain):
    """Test that summarize_log handles nonexistent log files."""
    # Create a command result with nonexistent log files
    log_files = LogFiles(stdout="/nonexistent/stdout.log", stderr="/nonexistent/stderr.log")
    command_result = CommandResultFactory(
        command="echo 'Hello, World!'",
        exit_code=0,
        log_files=log_files
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Summarize the log
    result = summarize_log(graph_state)

    # Check that the log was summarized correctly
    assert result.log_summary == "Mocked summary"

    # Check that the chain was invoked with the correct arguments
    mock_chain.invoke.assert_called_once()
    args = mock_chain.invoke.call_args[0][0]
    assert args["command"] == "echo 'Hello, World!'"
    assert args["exit_code"] == 0
    assert args["stdout"] == ""
    assert args["stderr"] == ""


def test_summarize_log_with_exception(mock_chain):
    """Test that summarize_log handles exceptions."""
    # Set up the mock chain to raise an exception
    mock_chain.invoke.side_effect = Exception("Mocked exception")

    # Create a command result
    command_result = CommandResultFactory(
        command="echo 'Hello, World!'",
        exit_code=0
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Summarize the log
    result = summarize_log(graph_state)

    # Check that the log summary contains the exception message
    assert "Error generating summary: Mocked exception" in result.log_summary
