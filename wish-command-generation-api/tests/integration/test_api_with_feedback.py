"""Integration tests for the API with feedback."""

import json
from unittest.mock import MagicMock, patch

import pytest
from wish_models.settings import Settings

from wish_command_generation_api.app import lambda_handler
from wish_command_generation_api.models import GeneratedCommand, GenerateResponse


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


@pytest.fixture
def mock_env_path():
    """Mock the environment path."""
    with patch("wish_models.settings.get_default_env_path") as mock_path:
        mock_path.return_value = "/mock/path/.env"
        yield mock_path


@pytest.fixture
def mock_settings():
    """Mock the settings object."""
    with patch("wish_models.settings.Settings") as mock_settings_class:
        mock_settings_instance = MagicMock()
        mock_settings_class.return_value = mock_settings_instance
        yield mock_settings_instance


def test_lambda_handler_with_feedback(mock_env_path, mock_settings):
    """Test the lambda handler with feedback."""
    # Arrange
    # Create a mock feedback
    act_result = [
        {
            "num": 1,
            "command": "nmap -p- 10.10.10.40",
            "state": "TIMEOUT",
            "exit_code": 1,
            "log_summary": "timeout",
            "log_files": {
                "stdout": "/tmp/stdout.log",
                "stderr": "/tmp/stderr.log"
            },
            "created_at": "2025-04-21T04:16:38.000Z"
        }
    ]

    # Create a mock event with feedback
    event = {
        "body": json.dumps({
            "query": "Conduct a full port scan on IP 10.10.10.40",
            "context": {"current_directory": "/home/user"},
            "act_result": act_result
        })
    }

    # Create a mock response
    mock_response = GenerateResponse(
        generated_command=GeneratedCommand(
            command="rustscan -a 10.10.10.40",
            explanation="This command performs a fast port scan using rustscan."
        )
    )

    # Mock the generate_command function
    with patch("wish_command_generation_api.app.generate_command", return_value=mock_response) as mock_generate:
        # Act
        response = lambda_handler(event, {})

        # Assert
        # Verify the response
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"

        body = json.loads(response["body"])
        assert body["generated_command"]["command"] == "rustscan -a 10.10.10.40"
        assert body["generated_command"]["explanation"] == "This command performs a fast port scan using rustscan."

        # Verify that generate_command was called with the correct parameters
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args

        # Check the request object
        request = args[0]
        assert request.query == "Conduct a full port scan on IP 10.10.10.40"
        assert request.context == {"current_directory": "/home/user"}
        assert len(request.act_result) == 1
        assert request.act_result[0].command == "nmap -p- 10.10.10.40"
        assert request.act_result[0].state.value == "TIMEOUT"
        assert request.act_result[0].exit_code == 1
        assert request.act_result[0].log_summary == "timeout"


def test_lambda_handler_with_network_error_feedback(mock_env_path, mock_settings):
    """Test the lambda handler with network error feedback."""
    # Arrange
    # Create a mock feedback
    act_result = [
        {
            "num": 1,
            "command": "nmap -p- 10.10.10.40",
            "state": "NETWORK_ERROR",
            "exit_code": 1,
            "log_summary": "Connection closed by peer",
            "log_files": {
                "stdout": "/tmp/stdout.log",
                "stderr": "/tmp/stderr.log"
            },
            "created_at": "2025-04-21T04:16:38.000Z"
        }
    ]

    # Create a mock event with feedback
    event = {
        "body": json.dumps({
            "query": "Conduct a full port scan on IP 10.10.10.40",
            "context": {"current_directory": "/home/user"},
            "act_result": act_result
        })
    }

    # Create a mock response
    mock_response = GenerateResponse(
        generated_command=GeneratedCommand(
            command="nmap -Pn -p- 10.10.10.40",
            explanation="This command performs a port scan while skipping host discovery."
        )
    )

    # Mock the generate_command function
    with patch("wish_command_generation_api.app.generate_command", return_value=mock_response) as mock_generate:
        # Act
        response = lambda_handler(event, {})

        # Assert
        # Verify the response
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"

        body = json.loads(response["body"])
        assert body["generated_command"]["command"] == "nmap -Pn -p- 10.10.10.40"
        assert body["generated_command"]["explanation"] == (
            "This command performs a port scan while skipping host discovery."
        )

        # Verify that generate_command was called with the correct parameters
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args

        # Check the request object
        request = args[0]
        assert request.query == "Conduct a full port scan on IP 10.10.10.40"
        assert request.context == {"current_directory": "/home/user"}
        assert len(request.act_result) == 1
        assert request.act_result[0].command == "nmap -p- 10.10.10.40"
        assert request.act_result[0].state.value == "NETWORK_ERROR"
        assert request.act_result[0].exit_code == 1
        assert request.act_result[0].log_summary == "Connection closed by peer"


def test_lambda_handler_with_multiple_feedback(mock_env_path, mock_settings):
    """Test the lambda handler with multiple feedback items."""
    # Arrange
    # Create a mock feedback with multiple items
    act_result = [
        {
            "num": 1,
            "command": "nmap -p1-1000 10.10.10.40",
            "state": "SUCCESS",
            "exit_code": 0,
            "log_summary": "Scan completed successfully",
            "log_files": {
                "stdout": "/tmp/stdout.log",
                "stderr": "/tmp/stderr.log"
            },
            "created_at": "2025-04-21T04:16:38.000Z"
        },
        {
            "num": 2,
            "command": "nmap -p1001-65535 10.10.10.40",
            "state": "TIMEOUT",
            "exit_code": 1,
            "log_summary": "timeout",
            "log_files": {
                "stdout": "/tmp/stdout.log",
                "stderr": "/tmp/stderr.log"
            },
            "created_at": "2025-04-21T04:16:38.000Z"
        }
    ]

    # Create a mock event with feedback
    event = {
        "body": json.dumps({
            "query": "Conduct a full port scan on IP 10.10.10.40",
            "context": {"current_directory": "/home/user"},
            "act_result": act_result
        })
    }

    # Create a mock response
    mock_response = GenerateResponse(
        generated_command=GeneratedCommand(
            command="rustscan -a 10.10.10.40 -r 1001-65535",
            explanation="This command performs a fast port scan on the remaining port range."
        )
    )

    # Mock the generate_command function
    with patch("wish_command_generation_api.app.generate_command", return_value=mock_response) as mock_generate:
        # Act
        response = lambda_handler(event, {})

        # Assert
        # Verify the response
        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"

        body = json.loads(response["body"])
        assert body["generated_command"]["command"] == "rustscan -a 10.10.10.40 -r 1001-65535"
        assert body["generated_command"]["explanation"] == (
            "This command performs a fast port scan on the remaining port range."
        )

        # Verify that generate_command was called with the correct parameters
        mock_generate.assert_called_once()
        args, kwargs = mock_generate.call_args

        # Check the request object
        request = args[0]
        assert request.query == "Conduct a full port scan on IP 10.10.10.40"
        assert request.context == {"current_directory": "/home/user"}
        assert len(request.act_result) == 2
        assert request.act_result[0].command == "nmap -p1-1000 10.10.10.40"
        assert request.act_result[0].state.value == "SUCCESS"
        assert request.act_result[1].command == "nmap -p1001-65535 10.10.10.40"
        assert request.act_result[1].state.value == "TIMEOUT"


def test_lambda_handler_with_error_response(mock_env_path, mock_settings):
    """Test the lambda handler with an error response from generate_command."""
    # Arrange
    # Create a mock feedback
    act_result = [
        {
            "num": 1,
            "command": "nmap -p- 10.10.10.40",
            "state": "TIMEOUT",
            "exit_code": 1,
            "log_summary": "timeout",
            "log_files": {
                "stdout": "/tmp/stdout.log",
                "stderr": "/tmp/stderr.log"
            },
            "created_at": "2025-04-21T04:16:38.000Z"
        }
    ]

    # Create a mock event with feedback
    event = {
        "body": json.dumps({
            "query": "Conduct a full port scan on IP 10.10.10.40",
            "context": {"current_directory": "/home/user"},
            "act_result": act_result
        })
    }

    # Create a mock response with an error
    mock_response = GenerateResponse(
        generated_command=GeneratedCommand(
            command="echo 'Command generation failed'",
            explanation="Error: Failed to generate command due to API error"
        ),
        error="Failed to generate command"
    )

    # Mock the generate_command function
    with patch("wish_command_generation_api.app.generate_command",
               return_value=mock_response) as mock_generate:
        # Act
        response = lambda_handler(event, {})

        # Use mock_generate to avoid F841 error
        assert mock_generate.called

        # Assert
        # Verify the response
        assert response["statusCode"] == 500
        assert response["headers"]["Content-Type"] == "application/json"

        body = json.loads(response["body"])
        assert body["error"] == "Failed to generate command"
