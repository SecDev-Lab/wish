"""Tests for the wish-log-analysis-api Lambda handler."""

import json
import pytest
from unittest.mock import MagicMock, patch

from wish_log_analysis_api.app import lambda_handler, analyze_command_result
from wish_log_analysis_api.models import AnalyzeRequest, AnalyzeResponse, GraphState
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory


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
        with patch("wish_log_analysis_api.app.create_log_analysis_graph", return_value=mock_graph):
            # Call the function
            request = AnalyzeRequest(command_result=command_result)
            response = analyze_command_result(request)

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
        with patch("wish_log_analysis_api.app.create_log_analysis_graph", return_value=mock_graph):
            # Call the function
            request = AnalyzeRequest(command_result=command_result)
            response = analyze_command_result(request)

            # Verify the response
            assert response.analyzed_command_result == command_result
            assert response.error == "Test error"


class TestLambdaHandler:
    """Tests for the Lambda handler."""

    def test_handler_success(self, lambda_event, analyzed_command_result):
        """Test successful handling of a Lambda event."""
        # Mock the analyze_command_result function
        with patch("wish_log_analysis_api.app.analyze_command_result") as mock_analyze:
            mock_analyze.return_value = AnalyzeResponse(
                analyzed_command_result=analyzed_command_result
            )

            # Call the handler
            response = lambda_handler(lambda_event, {})

            # Verify the response
            assert response["statusCode"] == 200
            assert response["headers"]["Content-Type"] == "application/json"
            
            body = json.loads(response["body"])
            assert "analyzed_command_result" in body
            assert body["analyzed_command_result"]["command"] == "ls -la"
            assert body["analyzed_command_result"]["state"] == "SUCCESS"
            assert body["analyzed_command_result"]["log_summary"] == "Listed files: file1.txt, file2.txt"

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
