"""Integration tests for library usage."""

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


@pytest.mark.integration
def test_end_to_end_analysis(mock_chat_openai, mock_str_output_parser):
    """End-to-end library usage test with mocked API calls"""
    # Create test log files
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
        stdout_file.write("Command executed successfully")
        stdout_path = stdout_file.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
        stderr_file.write("")
        stderr_path = stderr_file.name

    try:
        # Create command result
        log_files = LogFiles(stdout=Path(stdout_path), stderr=Path(stderr_path))
        command_result = CommandResult(
            num=1,
            command="echo 'test'",
            state=CommandState.DOING,
            exit_code=0,
            log_files=log_files,
            created_at=UtcDatetime.now(),
            finished_at=UtcDatetime.now()
        )

        # Configure mock responses
        mock_chain = MagicMock()
        mock_chat_openai.__or__.return_value = mock_chain
        mock_chain.invoke.side_effect = [
            "Command executed successfully. Output shows test message.",  # For log_summarization
            "SUCCESS"  # For command_state_classifier
        ]

        # Create a mock graph state for the result
        mock_result = GraphState(
            command_result=command_result,
            log_summary="Command executed successfully. Output shows test message.",
            command_state=CommandState.SUCCESS,
            analyzed_command_result=CommandResult(
                num=command_result.num,
                command=command_result.command,
                state=CommandState.SUCCESS,
                exit_code=command_result.exit_code,
                log_summary="Command executed successfully. Output shows test message.",
                log_files=command_result.log_files,
                created_at=command_result.created_at,
                finished_at=command_result.finished_at
            )
        )

        # Mock the graph
        with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph") as mock_create_graph:
            mock_graph = MagicMock()
            mock_graph.invoke.return_value = mock_result
            mock_create_graph.return_value = mock_graph

            # Create request
            request = AnalyzeRequest(command_result=command_result)

            # Create settings object
            settings_obj = Settings()

            # Run analysis
            response = analyze_command_result(request, settings_obj=settings_obj)

            # Verify results
            assert response is not None
            assert response.analyzed_command_result is not None
            assert response.analyzed_command_result.state == CommandState.SUCCESS
            assert response.analyzed_command_result.log_summary is not None
            assert "successfully" in response.analyzed_command_result.log_summary.lower()

    finally:
        # Cleanup
        os.unlink(stdout_path)
        os.unlink(stderr_path)


@pytest.mark.integration
def test_custom_config_integration(mock_chat_openai, mock_str_output_parser):
    """Test library usage with custom configuration and mocked API calls"""
    # Create test log files
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
        stdout_file.write("Error: command not found")
        stdout_path = stdout_file.name

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
        stderr_file.write("bash: unknown_command: command not found")
        stderr_path = stderr_file.name

    try:
        # Create command result
        log_files = LogFiles(stdout=Path(stdout_path), stderr=Path(stderr_path))
        command_result = CommandResult(
            num=1,
            command="unknown_command",
            state=CommandState.DOING,
            exit_code=127,
            log_files=log_files,
            created_at=UtcDatetime.now(),
            finished_at=UtcDatetime.now()
        )

        # Configure mock responses
        mock_chain = MagicMock()
        mock_chat_openai.__or__.return_value = mock_chain
        mock_chain.invoke.side_effect = [
            "Command 'unknown_command' not found in the system.",  # For log_summarization
            "COMMAND_NOT_FOUND"  # For command_state_classifier
        ]

        # Create a mock graph state for the result
        mock_result = GraphState(
            command_result=command_result,
            log_summary="Command 'unknown_command' not found in the system.",
            command_state=CommandState.COMMAND_NOT_FOUND,
            analyzed_command_result=CommandResult(
                num=command_result.num,
                command=command_result.command,
                state=CommandState.COMMAND_NOT_FOUND,
                exit_code=command_result.exit_code,
                log_summary="Command 'unknown_command' not found in the system.",
                log_files=command_result.log_files,
                created_at=command_result.created_at,
                finished_at=command_result.finished_at
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
                langchain_tracing_v2=True
            )

            # Create request
            request = AnalyzeRequest(command_result=command_result)

            # Create settings object
            settings_obj = Settings()

            # Run analysis with custom configuration
            response = analyze_command_result(request, settings_obj=settings_obj, config=config)

            # Verify results
            assert response is not None
            assert response.analyzed_command_result is not None
            assert response.analyzed_command_result.state == CommandState.COMMAND_NOT_FOUND
            assert response.analyzed_command_result.log_summary is not None
            assert "not found" in response.analyzed_command_result.log_summary.lower()

            # Verify the graph was created with the custom config
            mock_create_graph.assert_called_once_with(config=config, settings_obj=settings_obj)

    finally:
        # Cleanup
        os.unlink(stdout_path)
        os.unlink(stderr_path)
