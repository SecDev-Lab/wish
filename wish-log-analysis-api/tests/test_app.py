"""Tests for the wish-log-analysis-api Lambda handler."""

import json
from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result.command_state import CommandState
from wish_models.settings import Settings
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory

from wish_log_analysis_api.app import lambda_handler
from wish_log_analysis_api.core.analyzer import analyze_command_result
from wish_log_analysis_api.models import AnalyzeRequest, GraphState


# Mock OpenAI API calls globally for all tests in this file
@pytest.fixture(autouse=True)
def mock_openai_api():
    """Mock OpenAI API calls."""
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        # Create a mock instance
        mock_instance = MagicMock()
        # Configure the mock to return itself when piped
        mock_instance.__or__.return_value = mock_instance
        # Set the mock instance as the return value of the constructor
        mock_chat.return_value = mock_instance

        # Mock the chain.invoke method
        mock_chain = MagicMock()
        mock_instance.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = "Mocked response"

        # Mock StrOutputParser
        with patch("langchain_core.output_parsers.StrOutputParser") as mock_parser:
            # Create a mock instance
            mock_parser_instance = MagicMock()
            # Configure the mock to return itself when piped
            mock_parser_instance.__or__.return_value = mock_parser_instance
            # Set the mock instance as the return value of the constructor
            mock_parser.return_value = mock_parser_instance

            yield


@pytest.fixture
def command_result():
    """Create a test command result."""
    return CommandResultSuccessFactory.build(
        command="ls -la",
        stdout="file1.txt\nfile2.txt",
        stderr=None,
        exit_code=0,
        state=CommandState.DOING,
        log_summary=None,
    )


@pytest.fixture
def analyzed_command_result():
    """Create a test analyzed command result."""
    return CommandResultSuccessFactory.build(
        command="ls -la",
        stdout="file1.txt\nfile2.txt",
        stderr=None,
        exit_code=0,
        state=CommandState.SUCCESS,
        log_summary="Listed files: file1.txt, file2.txt",
    )


@pytest.fixture
def lambda_event(command_result):
    """Create a test Lambda event."""
    return {
        "body": json.dumps({
            "command_result": command_result.model_dump()
        })
    }


class TestAnalyzeCommandResult:
    """Tests for the analyze_command_result function."""

    def test_analyze_success(self, command_result, analyzed_command_result):
        """Test successful analysis of a command result."""
        # Mock the graph
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = GraphState(
            command_result=command_result,
            analyzed_command_result=analyzed_command_result,
            command_state=CommandState.SUCCESS,
            log_summary="Listed files: file1.txt, file2.txt",
        )

        # Mock the create_log_analysis_graph function
        with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph", return_value=mock_graph):
            # Call the function
            request = AnalyzeRequest(command_result=command_result)

            # Create settings object
            settings_obj = Settings()

            response = analyze_command_result(request, settings_obj=settings_obj)

            # Verify the response
            assert response.analyzed_command_result == analyzed_command_result
            assert response.error is None

            # Verify the graph was called with the correct initial state
            mock_graph.invoke.assert_called_once()
            args, _ = mock_graph.invoke.call_args
            assert args[0].command_result == command_result

    def test_analyze_error(self, command_result):
        """Test handling of errors during analysis."""
        # Mock the graph to raise an exception
        mock_graph = MagicMock()
        mock_graph.invoke.side_effect = Exception("Test error")

        # Mock the create_log_analysis_graph function
        with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph", return_value=mock_graph):
            # Call the function
            request = AnalyzeRequest(command_result=command_result)

            # Create settings object
            settings_obj = Settings()

            response = analyze_command_result(request, settings_obj=settings_obj)

            # Verify the response
            assert response.analyzed_command_result == command_result
            assert response.error == "Test error"


class TestLambdaHandler:
    """Tests for the Lambda handler."""

    def test_handler_success(self, lambda_event, analyzed_command_result, command_result):
        """Test successful handling of a Lambda event."""
        # Create a mock graph
        mock_graph = MagicMock()
        mock_result = GraphState(
            command_result=command_result,
            log_summary="Mocked log summary",
            command_state=CommandState.SUCCESS,
            analyzed_command_result=analyzed_command_result
        )
        mock_graph.invoke.return_value = mock_result

        # Mock create_log_analysis_graph to return our mock graph
        with patch("wish_log_analysis_api.core.analyzer.create_log_analysis_graph", return_value=mock_graph):
            # Mock model_validate
            with patch(
                "wish_log_analysis_api.models.AnalyzeRequest.model_validate",
                return_value=AnalyzeRequest(command_result=command_result)
            ):
                # Mock Settings
                with patch(
                    "wish_models.settings.Settings",
                    return_value=MagicMock()
                ):
                    # Call the handler
                    response = lambda_handler(lambda_event, {})

                    # Verify the response
                    assert response["statusCode"] == 200
                    assert response["headers"]["Content-Type"] == "application/json"

                    body = json.loads(response["body"])
                    assert "analyzed_command_result" in body
                    assert body["analyzed_command_result"]["command"] == "ls -la"
                    assert body["analyzed_command_result"]["state"] == "SUCCESS"
                    # Just check that log_summary exists, not its exact content
                    assert "log_summary" in body["analyzed_command_result"]

    def test_handler_invalid_request(self):
        """Test handling of an invalid request."""
        # Create an invalid event
        event = {
            "body": json.dumps({
                "invalid": "request"
            })
        }

        # Call the handler
        response = lambda_handler(event, {})

        # Verify the response
        assert response["statusCode"] == 500
        assert response["headers"]["Content-Type"] == "application/json"

        body = json.loads(response["body"])
        assert "error" in body

    def test_handler_error(self, lambda_event):
        """Test handling of errors during processing."""
        # Mock the analyze_command_result function to raise an exception
        with patch("wish_log_analysis_api.app.AnalyzeRequest.model_validate") as mock_validate:
            mock_validate.side_effect = Exception("Test error")

            # Call the handler
            response = lambda_handler(lambda_event, {})

            # Verify the response
            assert response["statusCode"] == 500
            assert response["headers"]["Content-Type"] == "application/json"

            body = json.loads(response["body"])
            assert "error" in body
            assert "Test error" in body["error"]
