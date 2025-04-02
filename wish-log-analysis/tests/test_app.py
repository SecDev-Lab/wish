"""Tests for the wish-log-analysis client."""

import json
import pytest
import requests
import requests_mock
from unittest.mock import patch

from wish_log_analysis.app import LogAnalysisClient, analyze_logs, analyze_result
from wish_models.command_result import CommandResult
from wish_models.command_result.command_state import CommandState
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory, CommandResultDoingFactory


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
        command_result = CommandResultDoingFactory.build(
            command="ls -la",
            log_files={"stdout": "file1.txt\nfile2.txt", "stderr": ""},
            exit_code=0,
            log_summary=None,
        )

        # Create the expected response
        analyzed_result = CommandResultSuccessFactory.build(
            command="ls -la",
            log_files={"stdout": "file1.txt\nfile2.txt", "stderr": ""},
            exit_code=0,
            log_summary="Listed files: file1.txt, file2.txt",
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
            assert result.summary == "Listed files: file1.txt, file2.txt"
            assert result.state == "SUCCESS"
            assert result.error_message is None

            # Verify the request
            assert m.last_request.json() == {
                "command_result": command_result.model_dump()
            }

    def test_analyze_api_error(self):
        """Test that the client handles API errors."""
        # Create a command result
        command_result = CommandResultDoingFactory.build(
            command="ls -la",
            log_files={"stdout": "file1.txt\nfile2.txt", "stderr": ""},
            exit_code=0,
            log_summary=None,
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

            # Verify the result
            assert result.summary == "解析結果なし"
            assert result.state == command_result.state
            assert result.error_message == "API error"

    def test_analyze_request_exception(self):
        """Test that the client handles request exceptions."""
        # Create a command result
        command_result = CommandResultDoingFactory.build(
            command="ls -la",
            log_files={"stdout": "file1.txt\nfile2.txt", "stderr": ""},
            exit_code=0,
            log_summary=None,
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

            # Verify the result
            assert result.summary == "APIリクエストに失敗しました"
            assert result.state == "error"
            assert "Connection error" in result.error_message


def test_analyze_result():
    """Test the analyze_result function."""
    # Create a command result
    command_result = CommandResultDoingFactory.build(
        command="ls -la",
        log_files={"stdout": "file1.txt\nfile2.txt", "stderr": ""},
        exit_code=0,
        log_summary=None,
    )

    # Create the expected response
    analyzed_result = CommandResultSuccessFactory.build(
        command="ls -la",
        log_files={"stdout": "file1.txt\nfile2.txt", "stderr": ""},
        exit_code=0,
        log_summary="Listed files: file1.txt, file2.txt",
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
        result = analyze_result(command_result)

        # Verify the result
        assert result.command == "ls -la"
        assert result.exit_code == 0
        assert result.state == CommandState.SUCCESS
        assert result.log_summary == "Listed files: file1.txt, file2.txt"
