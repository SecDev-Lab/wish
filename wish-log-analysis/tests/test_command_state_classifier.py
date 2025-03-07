"""Tests for command_state_classifier.py."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result.command_state import CommandState
from wish_models.command_result.log_files import LogFiles

from wish_log_analysis.nodes.command_state_classifier import classify_command_state
from wish_log_analysis.test_factories import CommandResultFactory, GraphStateFactory


@pytest.fixture
def mock_chain():
    """Mock the chain used in classify_command_state."""
    with patch("wish_log_analysis.nodes.command_state_classifier.PromptTemplate") as mock_prompt:
        with patch("wish_log_analysis.nodes.command_state_classifier.ChatOpenAI") as _:
            with patch("wish_log_analysis.nodes.command_state_classifier.StrOutputParser") as _:
                # Set up the mock chain
                mock_chain = MagicMock()
                mock_chain.invoke.return_value = "SUCCESS"

                # Create a mock for the pipe
                mock_pipe = MagicMock()
                mock_pipe.invoke.return_value = "SUCCESS"

                # Set up the mock prompt to return a mock pipe
                mock_prompt.from_template.return_value = MagicMock()
                mock_prompt.from_template.return_value.__or__.return_value = MagicMock()
                mock_prompt.from_template.return_value.__or__.return_value.__or__.return_value = mock_pipe

                yield mock_pipe


def test_classify_command_state_success(mock_chain):
    """Test that classify_command_state classifies a successful command correctly."""
    # Create a command result with exit code 0
    command_result = CommandResultFactory(
        command="echo 'Hello, World!'",
        exit_code=0
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Classify the command state
    result = classify_command_state(graph_state)

    # Check that the command state was classified correctly
    assert result.command_state == CommandState.SUCCESS

    # Check that the chain was invoked with the correct arguments
    mock_chain.invoke.assert_called_once()
    args = mock_chain.invoke.call_args[0][0]
    assert args["command"] == "echo 'Hello, World!'"
    assert args["exit_code"] == 0


def test_classify_command_state_command_not_found(mock_chain):
    """Test that classify_command_state classifies a command not found error correctly."""
    # Set up the mock chain to return COMMAND_NOT_FOUND
    mock_chain.invoke.return_value = "COMMAND_NOT_FOUND"

    # Create a command result with exit code 127
    command_result = CommandResultFactory(
        command="unknown_command",
        exit_code=127
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Classify the command state
    result = classify_command_state(graph_state)

    # Check that the command state was classified correctly
    assert result.command_state == CommandState.COMMAND_NOT_FOUND


def test_classify_command_state_file_not_found(mock_chain):
    """Test that classify_command_state classifies a file not found error correctly."""
    # Set up the mock chain to return FILE_NOT_FOUND
    mock_chain.invoke.return_value = "FILE_NOT_FOUND"

    # Create a command result with exit code 1
    command_result = CommandResultFactory(
        command="cat nonexistent.txt",
        exit_code=1
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Classify the command state
    result = classify_command_state(graph_state)

    # Check that the command state was classified correctly
    assert result.command_state == CommandState.FILE_NOT_FOUND


def test_classify_command_state_with_log_files(mock_chain):
    """Test that classify_command_state reads log files and classifies the command state correctly."""
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

        # Classify the command state
        result = classify_command_state(graph_state)

        # Check that the command state was classified correctly
        assert result.command_state == CommandState.SUCCESS

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


def test_classify_command_state_with_exception(mock_chain):
    """Test that classify_command_state handles exceptions."""
    # Set up the mock chain to raise an exception
    mock_chain.invoke.side_effect = Exception("Mocked exception")

    # Create a command result
    command_result = CommandResultFactory(
        command="echo 'Hello, World!'",
        exit_code=0
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Classify the command state
    result = classify_command_state(graph_state)

    # Check that the command state is set to API_ERROR in case of an exception
    assert result.command_state == CommandState.API_ERROR


def test_classify_command_state_invalid_response(mock_chain):
    """Test that classify_command_state handles invalid responses."""
    # Set up the mock chain to return an invalid response
    mock_chain.invoke.return_value = "INVALID_RESPONSE"

    # Create a command result
    command_result = CommandResultFactory(
        command="echo 'Hello, World!'",
        exit_code=0
    )

    # Create a graph state
    graph_state = GraphStateFactory.create_with_command_result(command_result)

    # Classify the command state
    result = classify_command_state(graph_state)

    # Check that the command state is set to OTHERS for invalid responses
    assert result.command_state == CommandState.OTHERS
