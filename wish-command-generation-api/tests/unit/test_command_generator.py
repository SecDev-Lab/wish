"""Unit tests for the command generator node."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models.settings import Settings

from wish_command_generation_api.models import GraphState
from wish_command_generation_api.nodes import command_generator


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return Settings()


@pytest.fixture
def sample_state():
    """Create a sample graph state for testing."""
    return GraphState(
        query="list all files in the current directory",
        context={"current_directory": "/home/user", "history": ["cd /home/user", "mkdir test"]},
    )


def test_generate_command_success(sample_state, settings):
    """Test successful command generation."""
    # Arrange
    mock_content = MagicMock()
    mock_content.content = "ls -la"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_content

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert result.command_candidates == ["ls -la"]
    assert mock_llm.invoke.call_count == 1
    # Verify that the template was called with the correct arguments
    mock_template.from_template.assert_called_once()


def test_generate_command_with_docs(sample_state, settings):
    """Test that documents are included in the prompt."""
    # Arrange
    mock_content = MagicMock()
    mock_content.content = "ls -la"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_content

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert result.command_candidates == ["ls -la"]
    # Check that the from_template method was called with the correct template
    mock_template.from_template.assert_called_once_with(command_generator.COMMAND_GENERATOR_PROMPT)


def test_generate_command_markdown_code_block(sample_state, settings):
    """Test command generation with markdown code block formatting."""
    # Arrange
    mock_content = MagicMock()
    mock_content.content = "```bash\nls -la\n```"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_content

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert result.command_candidates == ["ls -la"]


def test_generate_command_exception(sample_state, settings):
    """Test command generation with exception handling."""
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("Test error")

    # Act
    with patch("langchain_openai.ChatOpenAI", return_value=mock_llm):
        with patch("wish_command_generation_api.nodes.command_generator.logger") as mock_logger:
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert result.command_candidates == ["echo 'Command generation failed'"]
    assert result.api_error is True
    mock_logger.exception.assert_called_once()


def test_generate_command_preserve_state(sample_state, settings):
    """Test that the generator preserves other state fields."""
    # Arrange
    mock_content = MagicMock()
    mock_content.content = "ls -la"
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = mock_content

    # Add additional fields to the state
    sample_state.processed_query = "list all files including hidden ones"
    sample_state.is_retry = True
    sample_state.error_type = "TEST_ERROR"

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert result.query == "list all files in the current directory"
    assert result.context == {"current_directory": "/home/user", "history": ["cd /home/user", "mkdir test"]}
    assert result.processed_query == "list all files including hidden ones"
    assert result.command_candidates == ["ls -la"]
    assert result.is_retry is True
    assert result.error_type == "TEST_ERROR"
