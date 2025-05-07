"""Unit tests for the command generator node."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models.test_factories.settings_factory import SettingsFactory

from wish_command_generation_api.nodes import command_generator
from wish_command_generation_api.test_factories.graph_state_factory import GraphStateFactory


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return SettingsFactory()


@pytest.fixture
def sample_state():
    """Create a sample graph state for testing."""
    return GraphStateFactory(
        query="list all files in the current directory",
        context={
            "current_directory": "/home/user",
            "history": ["cd /home/user", "mkdir test"],
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"},
            "initial_timeout_sec": 60
        },
    )


def test_generate_command_success(sample_state, settings):
    """Test successful command generation."""
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "ls -la"

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "ls -la"
    assert result.command_candidates[0].timeout_sec == 60
    assert mock_llm.invoke.call_count == 1
    # Verify that the template was called with the correct arguments
    mock_template.from_template.assert_called_once()


def test_generate_command_with_docs(sample_state, settings):
    """Test that documents are included in the prompt."""
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "ls -la"

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "ls -la"
    assert result.command_candidates[0].timeout_sec == 60
    # Check that the from_template method was called with the correct template
    mock_template.from_template.assert_called_once_with(command_generator.COMMAND_GENERATOR_PROMPT)


def test_generate_command_markdown_code_block(sample_state, settings):
    """Test command generation with markdown code block formatting."""
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "```bash\nls -la\n```"

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "ls -la"
    assert result.command_candidates[0].timeout_sec == 60


def test_generate_command_exception(sample_state, settings):
    """Test command generation with exception handling."""
    # Arrange
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = Exception("Test error")
    mock_llm = MagicMock()
    mock_prompt = MagicMock()
    mock_prompt.__or__.return_value = mock_chain

    # Act & Assert
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = mock_prompt
            with pytest.raises(RuntimeError) as excinfo:
                command_generator.generate_command(sample_state, settings)

    # 例外のメッセージを確認
    assert "Error generating command" in str(excinfo.value)


def test_generate_command_preserve_state(settings):
    """Test that the generator preserves other state fields."""
    # Arrange
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = "ls -la"

    # Create state with additional fields
    sample_state = GraphStateFactory(
        query="list all files in the current directory",
        context={
            "current_directory": "/home/user",
            "history": ["cd /home/user", "mkdir test"],
            "target": {"rhost": "10.10.10.40"},
            "attacker": {"lhost": "192.168.1.5"},
            "initial_timeout_sec": 60
        },
        processed_query="list all files including hidden ones",
        is_retry=False,
        error_type="TEST_ERROR"
    )

    # Act
    with patch.object(command_generator, "ChatOpenAI", return_value=mock_llm):
        with patch.object(command_generator, "ChatPromptTemplate") as mock_template:
            mock_template.from_template.return_value = MagicMock()
            mock_template.from_template.return_value.__or__.return_value = mock_llm
            result = command_generator.generate_command(sample_state, settings)

    # Assert
    assert result.query == "list all files in the current directory"
    assert result.context == {
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"],
        "target": {"rhost": "10.10.10.40"},
        "attacker": {"lhost": "192.168.1.5"},
        "initial_timeout_sec": 60
    }
    assert result.processed_query == "list all files including hidden ones"
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "ls -la"
    assert result.command_candidates[0].timeout_sec == 60
    assert result.is_retry is False
    assert result.error_type == "TEST_ERROR"
