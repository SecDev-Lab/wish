"""Unit tests for the analyzer module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.command_result.log_files import LogFiles
from wish_models.settings import Settings
from wish_models.utc_datetime import UtcDatetime

from wish_log_analysis_api.config import AnalyzerConfig
from wish_log_analysis_api.core.analyzer import analyze_command_result
from wish_log_analysis_api.models import AnalyzeRequest, GraphState


@pytest.fixture
def sample_log_files():
    """Create sample log files for testing"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
        stdout_file.write("Sample stdout content")
        stdout_path = stdout_file.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
        stderr_file.write("Sample stderr content")
        stderr_path = stderr_file.name

    yield LogFiles(stdout=Path(stdout_path), stderr=Path(stderr_path))

    # Cleanup
    os.unlink(stdout_path)
    os.unlink(stderr_path)


@pytest.fixture
def sample_command_result(sample_log_files):
    """Create a sample command result for testing"""
    return CommandResult(
        num=1,
        command="ls -la",
        state="DOING",
        exit_code=0,
        log_files=sample_log_files,
        created_at=UtcDatetime.now(),
        finished_at=UtcDatetime.now()
    )


@pytest.fixture
def mock_chat_openai():
    """Create a mock ChatOpenAI instance"""
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        # Create a mock instance
        mock_instance = MagicMock()
        # Configure the mock to return itself when piped
        mock_instance.__or__.return_value = mock_instance
        # Set the mock instance as the return value of the constructor
        mock_chat.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_str_output_parser():
    """Create a mock StrOutputParser instance"""
    with patch("langchain_core.output_parsers.StrOutputParser") as mock_parser:
        # Create a mock instance
        mock_instance = MagicMock()
        # Configure the mock to return itself when piped
        mock_instance.__or__.return_value = mock_instance
        # Set the mock instance as the return value of the constructor
        mock_parser.return_value = mock_instance
        yield mock_instance


def test_analyze_command_result_with_mocks(sample_command_result, mock_chat_openai, mock_str_output_parser):
    """Test command result analysis with mocked API calls"""
    # Configure mocks for the chain
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain

    # Configure mock responses
    mock_chain.invoke.side_effect = [
        "This is a mock summary of the command output",  # For log_summarization
        "SUCCESS"  # For command_state_classifier
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        command_result=sample_command_result,
        log_summary="This is a mock summary of the command output",
        command_state=CommandState.SUCCESS,
        analyzed_command_result=CommandResult(
            num=sample_command_result.num,
            command=sample_command_result.command,
            state=CommandState.SUCCESS,
            exit_code=sample_command_result.exit_code,
            log_summary="This is a mock summary of the command output",
            log_files=sample_command_result.log_files,
            created_at=sample_command_result.created_at,
            finished_at=sample_command_result.finished_at
        )
    )

    # Mock the graph
    with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph

        # Create request
        request = AnalyzeRequest(command_result=sample_command_result)

        # Create settings object
        settings_obj = Settings()

        # Run analysis
        response = analyze_command_result(request, settings_obj=settings_obj)

        # Verify results
        assert response is not None
        assert response.analyzed_command_result is not None
        assert response.analyzed_command_result.log_summary == "This is a mock summary of the command output"
        assert response.analyzed_command_result.state == CommandState.SUCCESS
        assert response.error is None

        # Verify the graph was created and invoked
        mock_create_graph.assert_called_once()
        mock_graph.invoke.assert_called_once()


def test_analyze_command_result_with_error(sample_command_result, mock_chat_openai, mock_str_output_parser):
    """Test command result analysis with error handling"""
    # Mock the graph to raise an exception
    with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.side_effect = Exception("Test error")
        mock_create_graph.return_value = mock_graph

        # Create request
        request = AnalyzeRequest(command_result=sample_command_result)

        # Create settings object
        settings_obj = Settings()

        # Run analysis
        response = analyze_command_result(request, settings_obj=settings_obj)

        # Verify results
        assert response is not None
        assert response.analyzed_command_result == sample_command_result
        assert response.error == "Test error"


def test_analyze_command_result_with_custom_config(sample_command_result, mock_chat_openai, mock_str_output_parser):
    """Test command result analysis with custom configuration"""
    # Configure mock responses
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain
    mock_chain.invoke.side_effect = [
        "This is a mock summary with custom config",
        "SUCCESS"
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        command_result=sample_command_result,
        log_summary="This is a mock summary with custom config",
        command_state=CommandState.SUCCESS,
        analyzed_command_result=CommandResult(
            num=sample_command_result.num,
            command=sample_command_result.command,
            state=CommandState.SUCCESS,
            exit_code=sample_command_result.exit_code,
            log_summary="This is a mock summary with custom config",
            log_files=sample_command_result.log_files,
            created_at=sample_command_result.created_at,
            finished_at=sample_command_result.finished_at
        )
    )

    # Mock the graph
    with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph

        # Create custom configuration
        config = AnalyzerConfig(
            openai_model="gpt-3.5-turbo",  # Use lightweight model for testing
        )

        # Create request
        request = AnalyzeRequest(command_result=sample_command_result)

        # Create settings object
        settings_obj = Settings()

        # Run analysis
        response = analyze_command_result(request, settings_obj=settings_obj, config=config)

        # Verify results
        assert response is not None
        assert response.analyzed_command_result is not None
        assert response.analyzed_command_result.log_summary == "This is a mock summary with custom config"
        assert response.analyzed_command_result.state == CommandState.SUCCESS
        assert response.error is None

        # Verify the graph was created with the custom config
        mock_create_graph.assert_called_once_with(config=config, settings_obj=settings_obj)


def test_analyze_command_result_with_default_config(sample_command_result, mock_chat_openai, mock_str_output_parser):
    """Test command result analysis with default configuration"""
    # Configure mock responses
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain
    mock_chain.invoke.side_effect = [
        "This is a mock summary with default config",
        "SUCCESS"
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        command_result=sample_command_result,
        log_summary="This is a mock summary with default config",
        command_state=CommandState.SUCCESS,
        analyzed_command_result=CommandResult(
            num=sample_command_result.num,
            command=sample_command_result.command,
            state=CommandState.SUCCESS,
            exit_code=sample_command_result.exit_code,
            log_summary="This is a mock summary with default config",
            log_files=sample_command_result.log_files,
            created_at=sample_command_result.created_at,
            finished_at=sample_command_result.finished_at
        )
    )

    # Mock the graph
    with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph

        # Create request
        request = AnalyzeRequest(command_result=sample_command_result)

        # Create settings object
        settings_obj = Settings()

        # Run analysis
        response = analyze_command_result(request, settings_obj=settings_obj)

        # Verify results
        assert response is not None
        assert response.analyzed_command_result is not None
        assert response.analyzed_command_result.log_summary == "This is a mock summary with default config"
        assert response.analyzed_command_result.state == CommandState.SUCCESS
        assert response.error is None

        # Verify the graph was created with default config (None)
        mock_create_graph.assert_called_once_with(config=None, settings_obj=settings_obj)
