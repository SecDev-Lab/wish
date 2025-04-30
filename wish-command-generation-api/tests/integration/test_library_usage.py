"""Integration tests for library usage."""

import pytest
from wish_models.settings import Settings

from wish_command_generation_api.config import GeneratorConfig
from wish_command_generation_api.core.generator import generate_commands
from wish_command_generation_api.models import GenerateRequest


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


@pytest.mark.integration
def test_end_to_end_generation(settings):
    """End-to-end library usage test with real API calls."""
    # Create sample query and context
    query = "list all files in the current directory"
    context = {
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"],
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"}
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
    assert any(term in response.generated_commands[0].explanation.lower() for term in ["file", "list", "directory"])


@pytest.mark.integration
def test_custom_config_integration(settings):
    """Test library usage with custom configuration and real API calls."""
    # Create sample query and context
    query = "find all text files in the system"
    context = {
        "current_directory": "/home/user",
        "history": ["cd /home/user"],
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"}
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
    assert any(term in response.generated_commands[0].explanation.lower() for term in ["find", "text", "file"])


@pytest.mark.integration
def test_complex_query_integration(settings):
    """Test library usage with a more complex query and real API calls."""
    # Create sample query and context
    query = "find all python files modified in the last 7 days and count them"
    context = {
        "current_directory": "/home/user/projects",
        "history": ["cd /home/user/projects", "ls"],
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"}
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
    assert any(term in response.generated_commands[0].command_input.command
               for term in ["mtime", "ctime", "atime", "newer"])
    assert any(term in response.generated_commands[0].command_input.command for term in ["wc", "count", "|"])
    assert response.generated_commands[0].explanation is not None
    assert any(
        term in response.generated_commands[0].explanation.lower()
        for term in ["python", "file", "day", "count"]
    )
