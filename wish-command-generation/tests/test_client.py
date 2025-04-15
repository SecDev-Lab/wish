"""Tests for the command generation client."""

import json
from unittest.mock import MagicMock, patch

import pytest
import requests
import requests_mock

from wish_command_generation.client import CommandGenerationClient, generate_command
from wish_command_generation.config import ClientConfig
from wish_command_generation.models import GeneratedCommand, GenerateResponse


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return ClientConfig(api_base_url="http://test-api.example.com")


@pytest.fixture
def sample_query():
    """Create a sample query for testing."""
    return "list all files in the current directory"


@pytest.fixture
def sample_context():
    """Create a sample context for testing."""
    return {
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }


@pytest.fixture
def sample_response():
    """Create a sample API response."""
    return {
        "generated_command": {
            "command": "ls -la",
            "explanation": "This command lists all files in the current directory, including hidden files."
        }
    }


def test_client_initialization():
    """Test client initialization."""
    # Test with default config
    client = CommandGenerationClient()
    assert client.config.api_base_url == "http://localhost:3000"
    assert client.config.generate_endpoint == "http://localhost:3000/generate"

    # Test with custom config
    config = ClientConfig(api_base_url="https://custom-api.example.com")
    client = CommandGenerationClient(config)
    assert client.config.api_base_url == "https://custom-api.example.com"
    assert client.config.generate_endpoint == "https://custom-api.example.com/generate"


def test_generate_command_success(mock_config, sample_query, sample_context, sample_response):
    """Test successful command generation."""
    with requests_mock.Mocker() as m:
        # Mock the API response
        m.post(
            "http://test-api.example.com/generate",
            json=sample_response,
            status_code=200
        )

        # Create client and generate command
        client = CommandGenerationClient(mock_config)
        response = client.generate_command(sample_query, sample_context)

        # Verify the response
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "ls -la"
        assert "hidden files" in response.generated_command.explanation
        assert response.error is None

        # Verify the request
        assert m.called
        assert m.call_count == 1
        request = m.last_request
        assert request.method == "POST"
        assert request.url == "http://test-api.example.com/generate"
        assert request.headers["Content-Type"] == "application/json"

        # Verify the request body
        body = json.loads(request.body)
        assert body["query"] == sample_query
        assert body["context"] == sample_context


def test_generate_command_http_error(mock_config, sample_query):
    """Test handling of HTTP errors."""
    with requests_mock.Mocker() as m:
        # Mock a server error
        m.post(
            "http://test-api.example.com/generate",
            status_code=500,
            text="Internal Server Error"
        )

        # Create client and generate command
        client = CommandGenerationClient(mock_config)
        response = client.generate_command(sample_query)

        # Verify the response
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "echo 'Command generation failed'"
        assert "API error" in response.generated_command.explanation
        assert response.error is not None


def test_generate_command_connection_error(mock_config, sample_query):
    """Test handling of connection errors."""
    with patch("requests.post") as mock_post:
        # Mock a connection error
        mock_post.side_effect = requests.ConnectionError("Connection refused")

        # Create client and generate command
        client = CommandGenerationClient(mock_config)
        response = client.generate_command(sample_query)

        # Verify the response
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "echo 'Command generation failed'"
        assert "Connection refused" in response.generated_command.explanation
        assert response.error is not None


def test_generate_command_invalid_json(mock_config, sample_query):
    """Test handling of invalid JSON responses."""
    with requests_mock.Mocker() as m:
        # Mock an invalid JSON response
        m.post(
            "http://test-api.example.com/generate",
            text="Not a JSON response",
            status_code=200
        )

        # Create client and generate command
        client = CommandGenerationClient(mock_config)
        response = client.generate_command(sample_query)

        # Verify the response
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "echo 'Command generation failed'"
        assert "Failed to generate command due to API error" in response.generated_command.explanation
        assert response.error is not None


def test_convenience_function(sample_query, sample_context, sample_response):
    """Test the convenience function for generating commands."""
    with patch("wish_command_generation.client.CommandGenerationClient") as mock_client_class:
        # Create a mock client instance
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock the generate_command method
        mock_response = GenerateResponse(
            generated_command=GeneratedCommand(
                command="ls -la",
                explanation="This command lists all files in the current directory, including hidden files."
            )
        )
        mock_client.generate_command.return_value = mock_response

        # Call the convenience function
        response = generate_command(sample_query, sample_context)

        # Verify the response
        assert response is mock_response

        # Verify the client was created and called correctly
        mock_client_class.assert_called_once()
        mock_client.generate_command.assert_called_once_with(sample_query, sample_context)
