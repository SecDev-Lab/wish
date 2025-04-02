"""Tests for the wish-log-analysis client."""

import json
import pytest
import requests_mock
from unittest.mock import patch

from wish_log_analysis.app import LogAnalysisClient, analyze_command_result
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.test_factories.command_result_factory import CommandResultFactory


class TestLogAnalysisClient:
    """Tests for the LogAnalysisClient class."""

    def test_init_default_url(self):
        """Test that the client initializes with the default URL."""
        client = LogAnalysisClient()
        assert client.api_url == "http://localhost:3000/analyze"

    def test_init_custom_url(self):
        """Test that the client initializes with a custom URL."""
        client = LogAnalysisClient("https://example.com/api")
        assert client.api_url == "https://example.com/api"

    def test_init_env_var(self):
        """Test that the client initializes with the URL from an environment variable."""
        with patch.dict("os.environ", {"WISH_LOG_ANALYSIS_API_URL": "https://api.example.com"}):
            client = LogAnalysisClient()
            assert client.api_url == "https://api.example.com"

    def test_analyze_success(self):
        """Test that the client successfully analyzes a command result."""
        # Create a command result
        command_result = CommandResultFactory.build(
            command="ls -la",
            stdout="file1.txt\nfile2.txt",
            stderr=None,
            exit_code=0,
            command_state=None,
            summary=None,
        )

        # Create the expected response
        analyzed_result = CommandResultFactory.build(
            command="ls -la",
            stdout="file1.txt\nfile2.txt",
            stderr=None,
            exit_code=0,
            command_state=CommandState.SUCCESS,
            summary="Listed files: file1.txt, file2.txt",
        )

        # Mock the API response
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:3000/analyze",
                json={
                    "analyzed_command_result": analyzed_result.model_dump(),
                    "error": None,
                },
            )

            # Test the client
            client = LogAnalysisClient()
            result = client.analyze(command_result)

            # Verify the result
            assert result.command == "ls -la"
            assert result.stdout == "file1.txt\nfile2.txt"
            assert result.stderr is None
            assert result.exit_code == 0
            assert result.command_state == CommandState.SUCCESS
            assert result.summary == "Listed files: file1.txt, file2.txt"

            # Verify the request
            assert m.last_request.json() == {
                "command_result": command_result.model_dump()
            }

    def test_analyze_api_error(self):
        """Test that the client handles API errors."""
        # Create a command result
        command_result = CommandResultFactory.build(
            command="ls -la",
            stdout="file1.txt\nfile2.txt",
            stderr=None,
            exit_code=0,
            command_state=None,
            summary=None,
        )

        # Mock the API response
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:3000/analyze",
                json={
                    "analyzed_command_result": command_result.model_dump(),
                    "error": "API error",
                },
            )

            # Test the client
            client = LogAnalysisClient()
            result = client.analyze(command_result)

            # Verify that the original command result is returned
            assert result == command_result

    def test_analyze_request_exception(self):
        """Test that the client handles request exceptions."""
        # Create a command result
        command_result = CommandResultFactory.build(
            command="ls -la",
            stdout="file1.txt\nfile2.txt",
            stderr=None,
            exit_code=0,
            command_state=None,
            summary=None,
        )

        # Mock the API response
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:3000/analyze",
                exc=requests.RequestException("Connection error"),
            )

            # Test the client
            client = LogAnalysisClient()
            result = client.analyze(command_result)

            # Verify that the original command result is returned
            assert result == command_result


def test_analyze_command_result():
    """Test the analyze_command_result function."""
    # Create a command result
    command_result = CommandResultFactory.build(
        command="ls -la",
        stdout="file1.txt\nfile2.txt",
        stderr=None,
        exit_code=0,
        command_state=None,
        summary=None,
    )

    # Create the expected response
    analyzed_result = CommandResultFactory.build(
        command="ls -la",
        stdout="file1.txt\nfile2.txt",
        stderr=None,
        exit_code=0,
        command_state=CommandState.SUCCESS,
        summary="Listed files: file1.txt, file2.txt",
    )

    # Mock the API response
    with requests_mock.Mocker() as m:
        m.post(
            "http://localhost:3000/analyze",
            json={
                "analyzed_command_result": analyzed_result.model_dump(),
                "error": None,
            },
        )

        # Test the function
        result = analyze_command_result(command_result)

        # Verify the result
        assert result.command == "ls -la"
        assert result.stdout == "file1.txt\nfile2.txt"
        assert result.stderr is None
        assert result.exit_code == 0
        assert result.command_state == CommandState.SUCCESS
        assert result.summary == "Listed files: file1.txt, file2.txt"
