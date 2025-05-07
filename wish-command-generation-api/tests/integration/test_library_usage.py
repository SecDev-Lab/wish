"""Integration tests for library usage."""

import pytest
from unittest.mock import patch, MagicMock
from wish_models.settings import Settings
from wish_models.command_result import CommandInput

from wish_command_generation_api.config import GeneratorConfig
from wish_command_generation_api.core.generator import generate_commands
from wish_command_generation_api.models import GenerateRequest, GenerateResponse, GeneratedCommand


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


@pytest.mark.integration
@patch('wish_command_generation_api.core.generator.create_command_generation_graph')
def test_end_to_end_generation(mock_create_graph, settings):
    """End-to-end library usage test with mocked API calls."""
    # モックの設定
    mock_graph = MagicMock()
    mock_result = MagicMock()
    mock_result.generated_commands = [
        GeneratedCommand(
            command_input=CommandInput(command="ls -la", timeout_sec=60),
            explanation="Lists all files in the current directory including hidden files"
        )
    ]
    mock_graph.invoke.return_value = mock_result
    mock_create_graph.return_value = mock_graph

    # Create sample query and context
    query = "list all files in the current directory"
    context = {
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"],
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"},
        "initial_timeout_sec": 60
    }

    # Create request
    request = GenerateRequest(query=query, context=context)

    # Run generation
    response = generate_commands(request, settings_obj=settings)

    # Verify results
    assert response is not None
    assert response.generated_commands is not None
    assert len(response.generated_commands) > 0
    assert "ls" in response.generated_commands[0].command_input.command
    assert response.generated_commands[0].explanation is not None
    assert response.generated_commands[0].command_input.timeout_sec == 60


@pytest.mark.integration
@patch('wish_command_generation_api.core.generator.create_command_generation_graph')
def test_custom_config_integration(mock_create_graph, settings):
    """Test library usage with custom configuration and mocked API calls."""
    # モックの設定
    mock_graph = MagicMock()
    mock_result = MagicMock()
    mock_result.generated_commands = [
        GeneratedCommand(
            command_input=CommandInput(command="find / -name '*.txt'", timeout_sec=60),
            explanation="Finds all text files in the system"
        )
    ]
    mock_graph.invoke.return_value = mock_result
    mock_create_graph.return_value = mock_graph

    # Create sample query and context
    query = "find all text files in the system"
    context = {
        "current_directory": "/home/user",
        "history": ["cd /home/user"],
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"},
        "initial_timeout_sec": 60
    }

    # Create custom configuration
    config = GeneratorConfig(
        openai_model="gpt-4o",  # Specify model explicitly
        langchain_tracing_v2=True
    )

    # Create request
    request = GenerateRequest(query=query, context=context)

    # Run generation with custom configuration
    response = generate_commands(request, settings_obj=settings, config=config)

    # Verify results
    assert response is not None
    assert response.generated_commands is not None
    assert len(response.generated_commands) > 0
    assert "find" in response.generated_commands[0].command_input.command
    assert "txt" in response.generated_commands[0].command_input.command
    assert response.generated_commands[0].explanation is not None
    assert response.generated_commands[0].command_input.timeout_sec == 60


@pytest.mark.integration
@patch('wish_command_generation_api.core.generator.create_command_generation_graph')
def test_complex_query_integration(mock_create_graph, settings):
    """Test library usage with a more complex query and mocked API calls."""
    # モックの設定
    mock_graph = MagicMock()
    mock_result = MagicMock()
    mock_result.generated_commands = [
        GeneratedCommand(
            command_input=CommandInput(
                command="find /home/user/projects -name '*.py' -mtime -7 | wc -l",
                timeout_sec=60
            ),
            explanation="Finds all Python files modified in the last 7 days and counts them"
        )
    ]
    mock_graph.invoke.return_value = mock_result
    mock_create_graph.return_value = mock_graph

    # Create sample query and context
    query = "find all python files modified in the last 7 days and count them"
    context = {
        "current_directory": "/home/user/projects",
        "history": ["cd /home/user/projects", "ls"],
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"},
        "initial_timeout_sec": 60
    }

    # Create request
    request = GenerateRequest(query=query, context=context)

    # Run generation
    response = generate_commands(request, settings_obj=settings)

    # Verify results
    assert response is not None
    assert response.generated_commands is not None
    assert len(response.generated_commands) > 0
    assert "find" in response.generated_commands[0].command_input.command
    assert ".py" in response.generated_commands[0].command_input.command
    assert "mtime" in response.generated_commands[0].command_input.command
    assert "|" in response.generated_commands[0].command_input.command
    assert response.generated_commands[0].explanation is not None
    assert response.generated_commands[0].command_input.timeout_sec == 60
