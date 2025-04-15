"""Integration tests for library usage."""

from unittest.mock import MagicMock, patch

import pytest

from wish_command_generation_api.config import GeneratorConfig
from wish_command_generation_api.core.generator import generate_command
from wish_command_generation_api.models import GeneratedCommand, GenerateRequest, GraphState


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


@pytest.mark.integration
def test_end_to_end_generation(mock_chat_openai):
    """End-to-end library usage test with mocked API calls"""
    # Create sample query and context
    query = "list all files in the current directory"
    context = {
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }

    # Configure mock responses
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain
    mock_chain.invoke.side_effect = [
        MagicMock(content="list all files including hidden ones"),  # For query_processor
        MagicMock(content="ls -la"),  # For command_generator
        MagicMock(content="This command lists all files in the current directory, including hidden files.")
        # For result_formatter
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        query=query,
        context=context,
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
        request = GenerateRequest(query=query, context=context)

        # Run generation
        response = generate_command(request)

        # Verify results
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "ls -la"
        assert response.generated_command.explanation is not None
        assert "hidden files" in response.generated_command.explanation.lower()


@pytest.mark.integration
def test_custom_config_integration(mock_chat_openai):
    """Test library usage with custom configuration and mocked API calls"""
    # Create sample query and context
    query = "find all text files in the system"
    context = {
        "current_directory": "/home/user",
        "history": ["cd /home/user"]
    }

    # Configure mock responses
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain
    mock_chain.invoke.side_effect = [
        MagicMock(content="find text files in the system"),  # For query_processor
        MagicMock(content="find / -name '*.txt'"),  # For command_generator
        MagicMock(content="This command searches for all .txt files starting from the root directory.")
        # For result_formatter
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        query=query,
        context=context,
        processed_query="find text files in the system",
        command_candidates=["find / -name '*.txt'"],
        generated_command=GeneratedCommand(
            command="find / -name '*.txt'",
            explanation="This command searches for all .txt files starting from the root directory."
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
            langchain_tracing_v2=True
        )

        # Create request
        request = GenerateRequest(query=query, context=context)

        # Run generation with custom configuration
        response = generate_command(request, config=config)

        # Verify results
        assert response is not None
        assert response.generated_command is not None
        assert response.generated_command.command == "find / -name '*.txt'"
        assert response.generated_command.explanation is not None
        assert "searches" in response.generated_command.explanation.lower()

        # Verify the graph was created with the custom config
        mock_create_graph.assert_called_once_with(config=config)


@pytest.mark.integration
def test_complex_query_integration(mock_chat_openai):
    """Test library usage with a more complex query and mocked API calls"""
    # Create sample query and context
    query = "find all python files modified in the last 7 days and count them"
    context = {
        "current_directory": "/home/user/projects",
        "history": ["cd /home/user/projects", "ls"]
    }

    # Configure mock responses
    mock_chain = MagicMock()
    mock_chat_openai.__or__.return_value = mock_chain
    mock_chain.invoke.side_effect = [
        MagicMock(content="find recent python files and count them"),  # For query_processor
        MagicMock(content="find . -name '*.py' -mtime -7 | wc -l"),  # For command_generator
        MagicMock(
            content="This command finds all Python files (*.py) modified in the last 7 days "
                   "in the current directory and its subdirectories, then counts them using wc -l."
        )  # For result_formatter
    ]

    # Create a mock graph state for the result
    mock_result = GraphState(
        query=query,
        context=context,
        processed_query="find recent python files and count them",
        command_candidates=["find . -name '*.py' -mtime -7 | wc -l"],
        generated_command=GeneratedCommand(
            command="find . -name '*.py' -mtime -7 | wc -l",
            explanation="This command finds all Python files (*.py) modified in the last 7 days "
                        "in the current directory and its subdirectories, then counts them using wc -l."
        )
    )

    # Mock the graph
    with patch("wish_command_generation_api.core.generator.create_command_generation_graph") as mock_create_graph:
        mock_graph = MagicMock()
        mock_graph.invoke.return_value = mock_result
        mock_create_graph.return_value = mock_graph

        # Create request
        request = GenerateRequest(query=query, context=context)

        # Run generation
        response = generate_command(request)

        # Verify results
        assert response is not None
        assert response.generated_command is not None
        assert "find" in response.generated_command.command
        assert "*.py" in response.generated_command.command
        assert "wc -l" in response.generated_command.command
        assert response.generated_command.explanation is not None
        assert "python files" in response.generated_command.explanation.lower()
