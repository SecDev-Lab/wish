"""Unit tests for the network error handler node."""

from unittest.mock import MagicMock, patch

import pytest
from wish_models.command_result import CommandState
from wish_models.test_factories.command_input_factory import CommandInputFactory
from wish_models.test_factories.settings_factory import SettingsFactory

from wish_command_generation_api.nodes import network_error_handler
from wish_command_generation_api.test_factories.graph_state_factory import GraphStateFactory


@pytest.fixture
def settings():
    """Create a settings object for testing."""
    return SettingsFactory()


@pytest.fixture
def mock_network_error_response():
    """Create a mock response for network error handling."""
    return "nmap -p- 10.10.10.40"


def test_handle_network_error_no_error(settings):
    """Test handling network error when there is no error."""
    # Arrange
    state = GraphStateFactory(query="test query", context={})

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


def test_handle_network_error_not_network_error(settings):
    """Test handling network error when the error is not a network error."""
    # Arrange
    state = GraphStateFactory.create_with_timeout_error(
        query="test query",
        command="test command"
    )

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result == state  # Should return the original state unchanged


def test_handle_network_error_success(settings, mock_network_error_response):
    """Test successful handling of a network error."""
    # Create a state with a network error
    state = GraphStateFactory.create_with_network_error(
        query="test_handle_network_error_success",
        command="nmap -p- 10.10.10.40",
        log_summary="Connection closed by peer"
    )

    # モックを使用してLLMの呼び出しをバイパス
    with patch.object(network_error_handler, "ChatOpenAI") as mock_llm_class:
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm

        # StrOutputParserをモック
        with patch.object(network_error_handler, "StrOutputParser") as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser

            # チェーンの結果をモック
            mock_chain = MagicMock()
            mock_chain.invoke.return_value = mock_network_error_response

            # チェーン作成をモック
            mock_prompt = MagicMock()
            with patch.object(network_error_handler, "ChatPromptTemplate") as mock_prompt_template:
                mock_prompt_template.from_template.return_value = mock_prompt
                mock_prompt.__or__.return_value = mock_llm
                mock_llm.__or__.return_value = mock_parser
                mock_parser.invoke = mock_chain.invoke

                # Act
                result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "nmap -p- 10.10.10.40"
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert len(result.failed_command_results) == 1
    assert result.failed_command_results[0].command == "nmap -p- 10.10.10.40"
    assert result.failed_command_results[0].state == CommandState.NETWORK_ERROR


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_with_dialog_avoidance_doc(mock_handler, settings):
    """Test that dialog avoidance document is included in the prompt."""
    # Create a state with a network error
    state = GraphStateFactory.create_with_network_error(
        query="List files in SMB share",
        command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1",
        log_summary="Connection closed by peer"
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1 -c 'ls'",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_network_error(
        query="List files in SMB share",
        command="smbclient -N //10.10.10.40/Users --option='client min protocol'=LANMAN1"
    )
    expected_result.command_candidates = command_candidates
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert "smbclient" in result.command_candidates[0].command
    assert "-c" in result.command_candidates[0].command  # 対話回避のドキュメントに従って -c オプションが追加されている


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_alternative_command(mock_handler, settings):
    """Test handling network error with an alternative command."""
    # Create a state with a network error
    context = {"test_handle_network_error_alternative_command": True}
    state = GraphStateFactory.create_with_network_error(
        query="test_handle_network_error_alternative_command",
        command="nmap -p- 10.10.10.40",
        log_summary="Connection closed by peer",
        context=context
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="nmap -Pn -p- 10.10.10.40",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_network_error(
        query="test_handle_network_error_alternative_command",
        command="nmap -p- 10.10.10.40",
        context=context
    )
    expected_result.command_candidates = command_candidates
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert len(result.command_candidates) == 1
    assert result.command_candidates[0].command == "nmap -Pn -p- 10.10.10.40"
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_json_error(mock_handler, settings):
    """Test handling network error when the LLM returns invalid JSON."""
    # Create a state with a network error
    context = {"test_handle_network_error_json_error": True}
    state = GraphStateFactory.create_with_network_error(
        query="test_handle_network_error_json_error",
        command="nmap -p- 10.10.10.40",
        log_summary="Connection closed by peer",
        context=context
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="echo 'Failed to generate network error handling command'",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_network_error(
        query="test_handle_network_error_json_error",
        command="nmap -p- 10.10.10.40",
        context=context
    )
    expected_result.command_candidates = command_candidates
    expected_result.api_error = True
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert "Failed to generate" in result.command_candidates[0].command
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_exception(mock_handler, settings):
    """Test handling exceptions during network error handling."""
    # Create a state with a network error
    state = GraphStateFactory.create_with_network_error(
        query="Conduct a full port scan on IP 10.10.10.40",
        command="nmap -p- 10.10.10.40",
        log_summary="Connection closed by peer"
    )

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="echo 'Error handling network error'",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_network_error(
        query="Conduct a full port scan on IP 10.10.10.40",
        command="nmap -p- 10.10.10.40"
    )
    expected_result.command_candidates = command_candidates
    expected_result.api_error = True
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert "Error handling network error" in result.command_candidates[0].command
    assert result.api_error is True


@patch("wish_command_generation_api.nodes.network_error_handler.handle_network_error")
def test_handle_network_error_preserve_state(mock_handler, settings):
    """Test that the network error handler preserves other state fields."""
    # Create a state with a network error and additional fields
    processed_query = "processed test query"
    context = {"current_directory": "/home/user"}

    state = GraphStateFactory.create_with_network_error(
        query="test_handle_network_error_preserve_state",
        command="nmap -p- 10.10.10.40",
        log_summary="Connection closed by peer",
        context=context
    )
    state.processed_query = processed_query

    # Mock the handler to return a modified state
    command_candidates = [
        CommandInputFactory(
            command="nmap -p- 10.10.10.40",
            timeout_sec=60
        )
    ]
    expected_result = GraphStateFactory.create_with_network_error(
        query="test_handle_network_error_preserve_state",
        command="nmap -p- 10.10.10.40",
        context=context
    )
    expected_result.processed_query = processed_query
    expected_result.command_candidates = command_candidates
    mock_handler.return_value = expected_result

    # Act
    result = network_error_handler.handle_network_error(state, settings)

    # Assert
    assert result.query == "test_handle_network_error_preserve_state"
    assert result.context == {"current_directory": "/home/user"}
    assert result.processed_query == processed_query
    assert result.is_retry is True
    assert result.error_type == "NETWORK_ERROR"
    assert len(result.failed_command_results) == 1
    assert result.failed_command_results[0].command == "nmap -p- 10.10.10.40"
    assert result.failed_command_results[0].state == CommandState.NETWORK_ERROR
