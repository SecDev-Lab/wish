"""Unit tests for the generator module."""

from unittest.mock import MagicMock, patch

import pytest

from wish_command_generation_api.config import GeneratorConfig
from wish_command_generation_api.core.generator import generate_command
from wish_command_generation_api.models import GeneratedCommand, GenerateRequest, GraphState
from wish_models.settings import Settings


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
def mock_chat_openai():
    """Create a mock ChatOpenAI instance"""
    with patch("langchain_openai.ChatOpenAI") as mock_chat:
        # Create a mock instance
        mock_instance = MagicMock()
        # Configure the mock to return itself when piped
        mock_instance.__or__.return_value = mock_instance
        # Set the mock instance as the return value of the constructor
        mock_chat.return_value = mock_instance
        yield mock_instance


def test_generate_command_with_mocks(sample_query, sample_context, mock_chat_openai):
    """Test command generation with mocked API calls"""
    # Configure mocks for the chain
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain

    # Configure mock responses
    mock_chain.invoke.side_effect = [
        MagicMock(content="list all files including hidden ones"),  # For query_processor
        MagicMock(content="ls -la"),  # For command_generator
        MagicMock(content="This command lists all files in the current directory, including hidden files.")
        # For result_formatter
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        query=sample_query,
        context=sample_context,
        processed_query="list all files including hidden ones",
        command_candidates=["ls -la"],
        generated_command=GeneratedCommand(
            command="ls -la",
            explanation="This command lists all files in the current directory, including hidden files."
        )
    )

    # Mock the graph
    with patch("wish_command_generation_api.core.generator.create_command_generation_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph

        # Create request
        request = GenerateRequest(query=sample_query, context=sample_context)

        # Create settings object
        settings_obj = Settings()

        # Run generation
        response = generate_command(request, settings_obj=settings_obj)

        # Verify results
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "ls -la"
        assert response.generated_command.explanation == (
            "This command lists all files in the current directory, including hidden files."
        )
        assert response.error is None

        # Verify the graph was created and invoked
        mock_create_graph.assert_called_once()
        mock_graph.invoke.assert_called_once()


def test_generate_command_with_error(sample_query, sample_context, mock_chat_openai):
    """Test command generation with error handling"""
    # Mock the graph to raise an exception
    with patch("wish_command_generation_api.core.generator.create_command_generation_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.side_effect = Exception("Test error")
        mock_create_graph.return_value = mock_graph

        # Create request
        request = GenerateRequest(query=sample_query, context=sample_context)

        # Create settings object
        settings_obj = Settings()

        # Run generation
        response = generate_command(request, settings_obj=settings_obj)

        # Verify results
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "echo 'Command generation failed'"
        assert "Test error" in response.generated_command.explanation
        assert response.error == "Test error"


def test_generate_command_with_custom_config(sample_query, sample_context, mock_chat_openai):
    """Test command generation with custom configuration"""
    # Configure mock responses
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain
    mock_chain.invoke.side_effect = [
        MagicMock(content="list all files with details"),  # For query_processor
        MagicMock(content="ls -l"),  # For command_generator
        MagicMock(content="This command lists all files with detailed information.")  # For result_formatter
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        query=sample_query,
        context=sample_context,
        processed_query="list all files with details",
        command_candidates=["ls -l"],
        generated_command=GeneratedCommand(
            command="ls -l",
            explanation="This command lists all files with detailed information."
        )
    )

    # Mock the graph
    with patch("wish_command_generation_api.core.generator.create_command_generation_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph

        # Create custom configuration
        config = GeneratorConfig(
            openai_model="gpt-3.5-turbo",  # Use lightweight model for testing
        )

        # Create request
        request = GenerateRequest(query=sample_query, context=sample_context)

        # Create settings object
        settings_obj = Settings()

        # Run generation
        response = generate_command(request, settings_obj=settings_obj, config=config)

        # Verify results
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "ls -l"
        assert response.generated_command.explanation == "This command lists all files with detailed information."
        assert response.error is None

        # Verify the graph was created with the custom config
        mock_create_graph.assert_called_once_with(settings_obj=settings_obj, config=config)


def test_generate_command_with_default_config(sample_query, sample_context, mock_chat_openai):
    """Test command generation with default configuration"""
    # Configure mock responses
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain
    mock_chain.invoke.side_effect = [
        MagicMock(content="list all files"),  # For query_processor
        MagicMock(content="ls"),  # For command_generator
        MagicMock(content="This command lists all files in the current directory.")  # For result_formatter
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        query=sample_query,
        context=sample_context,
        processed_query="list all files",
        command_candidates=["ls"],
        generated_command=GeneratedCommand(
            command="ls",
            explanation="This command lists all files in the current directory."
        )
    )

    # Mock the graph
    with patch("wish_command_generation_api.core.generator.create_command_generation_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph

        # Create request
        request = GenerateRequest(query=sample_query, context=sample_context)

        # Create settings object
        settings_obj = Settings()

        # Run generation
        response = generate_command(request, settings_obj=settings_obj)

        # Verify results
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "ls"
        assert response.generated_command.explanation == "This command lists all files in the current directory."
        assert response.error is None

        # Verify the graph was created with default config (None)
        mock_create_graph.assert_called_once_with(settings_obj=settings_obj, config=None)
