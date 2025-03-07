"""Test script for the command generation node."""

import json
from unittest.mock import MagicMock, patch

from wish_command_generation.nodes.command_generation import generate_commands
from wish_command_generation.test_factories.state_factory import GraphStateFactory


class TestCommandGeneration:
    """Test class for command generation functions."""

    def test_generate_commands_success(self):
        """Test that generate_commands correctly generates commands when the API call succeeds."""
        # Arrange
        state = GraphStateFactory.create_with_context(
            "Conduct a full port scan on IP 10.10.10.123.",
            ["nmap is a network scanning tool", "rustscan is a fast port scanner"]
        )

        # Set up the expected response
        expected_response = {
            "command_inputs": [
                {
                    "command": "rustscan -a 10.10.10.123",
                    "timeout_sec": None
                }
            ]
        }

        # Create a mock for the chain
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = json.dumps(expected_response)

        # Act
        with patch("wish_command_generation.nodes.command_generation.PromptTemplate") as mock_prompt_template:
            with patch("wish_command_generation.nodes.command_generation.ChatOpenAI") as mock_chat_openai:
                with patch(
                    "wish_command_generation.nodes.command_generation.StrOutputParser"
                ) as mock_str_output_parser:
                    # Set up the mocks to create the chain
                    mock_prompt = MagicMock()
                    mock_prompt_template.from_template.return_value = mock_prompt

                    mock_model = MagicMock()
                    mock_chat_openai.return_value = mock_model

                    mock_parser = MagicMock()
                    mock_str_output_parser.return_value = mock_parser

                    # Set up the chain creation
                    mock_prompt.__or__.return_value = mock_model
                    mock_model.__or__.return_value = mock_parser

                    # Make the chain invoke method return our expected response
                    mock_parser.invoke = mock_chain.invoke

                    result = generate_commands(state)

        # Assert
        assert len(result.command_inputs) == 1
        assert result.command_inputs[0].command == "rustscan -a 10.10.10.123"
        assert result.command_inputs[0].timeout_sec is None
        assert result.wish == state.wish
        assert result.context == state.context
        assert result.query == state.query

        # Verify the mock was called with the correct arguments
        mock_chain.invoke.assert_called_once()
        call_args = mock_chain.invoke.call_args[0][0]
        assert "task" in call_args
        assert call_args["task"] == "Conduct a full port scan on IP 10.10.10.123."
        assert "context" in call_args

    def test_generate_commands_api_error(self):
        """Test that generate_commands handles API errors gracefully."""
        # Arrange
        state = GraphStateFactory.create_with_specific_wish("Conduct a full port scan on IP 10.10.10.123.")

        # Create a mock for the chain
        mock_chain = MagicMock()
        error_message = "API rate limit exceeded"
        mock_chain.invoke.side_effect = Exception(error_message)

        # Act
        with patch("wish_command_generation.nodes.command_generation.PromptTemplate") as mock_prompt_template:
            with patch("wish_command_generation.nodes.command_generation.ChatOpenAI") as mock_chat_openai:
                with patch(
                    "wish_command_generation.nodes.command_generation.StrOutputParser"
                ) as mock_str_output_parser:
                    # Set up the mocks to create the chain
                    mock_prompt = MagicMock()
                    mock_prompt_template.from_template.return_value = mock_prompt

                    mock_model = MagicMock()
                    mock_chat_openai.return_value = mock_model

                    mock_parser = MagicMock()
                    mock_str_output_parser.return_value = mock_parser

                    # Set up the chain creation
                    mock_prompt.__or__.return_value = mock_model
                    mock_model.__or__.return_value = mock_parser

                    # Make the chain invoke method raise our exception
                    mock_parser.invoke = mock_chain.invoke

                    result = generate_commands(state)

        # Assert
        assert len(result.command_inputs) == 1
        assert f"Error generating commands: {error_message}" in result.command_inputs[0].command
        assert result.command_inputs[0].timeout_sec is None
        assert result.wish == state.wish
        assert result.context == state.context
        assert result.query == state.query

    def test_generate_commands_invalid_json(self):
        """Test that generate_commands handles invalid JSON responses gracefully."""
        # Arrange
        state = GraphStateFactory.create_with_specific_wish("Conduct a full port scan on IP 10.10.10.123.")

        # Create a mock for the chain
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "This is not valid JSON"

        # Act
        with patch("wish_command_generation.nodes.command_generation.PromptTemplate") as mock_prompt_template:
            with patch("wish_command_generation.nodes.command_generation.ChatOpenAI") as mock_chat_openai:
                with patch(
                    "wish_command_generation.nodes.command_generation.StrOutputParser"
                ) as mock_str_output_parser:
                    # Set up the mocks to create the chain
                    mock_prompt = MagicMock()
                    mock_prompt_template.from_template.return_value = mock_prompt

                    mock_model = MagicMock()
                    mock_chat_openai.return_value = mock_model

                    mock_parser = MagicMock()
                    mock_str_output_parser.return_value = mock_parser

                    # Set up the chain creation
                    mock_prompt.__or__.return_value = mock_model
                    mock_model.__or__.return_value = mock_parser

                    # Make the chain invoke method return invalid JSON
                    mock_parser.invoke = mock_chain.invoke

                    result = generate_commands(state)

        # Assert
        assert len(result.command_inputs) == 1
        assert "Error generating commands:" in result.command_inputs[0].command
        assert result.command_inputs[0].timeout_sec is None
        assert result.wish == state.wish
        assert result.context == state.context
        assert result.query == state.query
