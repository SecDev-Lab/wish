"""Tests for the wish-command-generation-api Lambda handler."""

import json
from unittest.mock import MagicMock, patch

import pytest

from wish_command_generation_api.app import lambda_handler
from wish_command_generation_api.core.generator import generate_command
from wish_command_generation_api.models import GenerateRequest, GraphState, GeneratedCommand


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
        mock_chain.invoke.return_value = MagicMock(content="Mocked response")

        yield


@pytest.fixture
def sample_query():
    """Create a sample query for testing"""
    return "list all files in the current directory"


@pytest.fixture
def sample_context():
    """Create a sample context for testing"""
    return {
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }


@pytest.fixture
def generated_command():
    """Create a test generated command."""
    return GeneratedCommand(
        command="ls -la",
        explanation="This command lists all files in the current directory, including hidden files."
    )


@pytest.fixture
def lambda_event(sample_query, sample_context):
    """Create a test Lambda event."""
    return {
        "body": json.dumps({
            "query": sample_query,
            "context": sample_context
        })
    }


class TestGenerateCommand:
    """Tests for the generate_command function."""

    def test_generate_success(self, sample_query, sample_context, generated_command):
        """Test successful generation of a command."""
        # Mock the graph
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = GraphState(
            query=sample_query,
            context=sample_context,
            processed_query="list all files including hidden ones",
            command_candidates=["ls -la"],
            generated_command=generated_command
        )

        # Mock the create_command_generation_graph function
        with patch("wish_command_generation_api.core.generator.create_command_generation_graph", return_value=mock_graph):
            # Call the function
            request = GenerateRequest(query=sample_query, context=sample_context)
            response = generate_command(request)

            # Verify the response
            assert response.generated_command == generated_command
            assert response.error is None

            # Verify the graph was called with the correct initial state
            mock_graph.invoke.assert_called_once()
            args, _ = mock_graph.invoke.call_args
            assert args[0].query == sample_query
            assert args[0].context == sample_context

    def test_generate_error(self, sample_query, sample_context):
        """Test handling of errors during generation."""
        # Mock the graph to raise an exception
        mock_graph = MagicMock()
        mock_graph.invoke.side_effect = Exception("Test error")

        # Mock the create_command_generation_graph function
        with patch("wish_command_generation_api.core.generator.create_command_generation_graph", return_value=mock_graph):
            # Call the function
            request = GenerateRequest(query=sample_query, context=sample_context)
            response = generate_command(request)

            # Verify the response
            assert response.generated_command is not None
            assert response.generated_command.command == "echo 'Command generation failed'"
            assert "Test error" in response.generated_command.explanation
            assert response.error == "Test error"


class TestLambdaHandler:
    """Tests for the Lambda handler."""

    def test_handler_success(self, lambda_event, sample_query, sample_context, generated_command):
        """Test successful handling of a Lambda event."""
        # Create a mock graph
        mock_graph = MagicMock()
        mock_result = GraphState(
            query=sample_query,
            context=sample_context,
            processed_query="list all files including hidden ones",
            command_candidates=["ls -la"],
            generated_command=generated_command
        )
        mock_graph.invoke.return_value = mock_result

        # Mock create_command_generation_graph to return our mock graph
        with patch("wish_command_generation_api.core.generator.create_command_generation_graph", return_value=mock_graph):
            # Mock model_validate
            with patch(
                "wish_command_generation_api.models.GenerateRequest.model_validate",
                return_value=GenerateRequest(query=sample_query, context=sample_context)
            ):
                # Call the handler
                response = lambda_handler(lambda_event, {})

                # Verify the response
                assert response["statusCode"] == 200
                assert response["headers"]["Content-Type"] == "application/json"

                body = json.loads(response["body"])
                assert "generated_command" in body
                assert body["generated_command"]["command"] == "ls -la"
                assert body["generated_command"]["explanation"] == "This command lists all files in the current directory, including hidden files."

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
        # Mock the GenerateRequest.model_validate function to raise an exception
        with patch("wish_command_generation_api.app.GenerateRequest.model_validate") as mock_validate:
            mock_validate.side_effect = Exception("Test error")

            # Call the handler
            response = lambda_handler(lambda_event, {})

            # Verify the response
            assert response["statusCode"] == 500
            assert response["headers"]["Content-Type"] == "application/json"

            body = json.loads(response["body"])
            assert "error" in body
            assert "Test error" in body["error"]
