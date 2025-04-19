"""Test script for the command generation node."""

import json
from unittest.mock import MagicMock, patch

import pytest
from wish_models.settings import Settings

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

                    # Create settings object
                    settings_obj = Settings()

                    result = generate_commands(state, settings_obj)

        # Assert
        assert len(result.command_inputs) == 1
        assert result.command_inputs[0].command == "rustscan -a 10.10.10.123"
        assert result.command_inputs[0].timeout_sec is None
        assert result.wish == state.wish
        assert result.context == state.context
        assert result.query == state.query

    def test_generate_commands_with_system_info(self):
        """Test that generate_commands correctly uses system information."""
        # Arrange
        state = GraphStateFactory.create_with_system_info(
            "List all hidden files in the current directory.",
            system_os="Windows",
            system_arch="AMD64",
            system_version="10.0.19044"
        )

        # Set up the expected response
        expected_response = {
            "command_inputs": [
                {
                    "command": "dir /a:h",
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

                    # Create settings object
                    settings_obj = Settings()

                    result = generate_commands(state, settings_obj)

        # Assert
        assert len(result.command_inputs) == 1
        assert result.command_inputs[0].command == "dir /a:h"
        assert result.command_inputs[0].timeout_sec is None

        # Verify the mock was called with the correct system info arguments
        mock_chain.invoke.assert_called_once()
        call_args = mock_chain.invoke.call_args[0][0]
        assert "system_os" in call_args
        assert call_args["system_os"] == "Windows"
        assert "system_arch" in call_args
        assert call_args["system_arch"] == "AMD64"
        assert "system_version" in call_args
        assert call_args["system_version"] == "10.0.19044"
        assert "task" in call_args
        assert call_args["task"] == "List all hidden files in the current directory."
        assert "context" in call_args

    def test_generate_commands_api_error(self):
        """Test that generate_commands raises CommandGenerationError for API errors."""
        # Arrange
        state = GraphStateFactory.create_with_specific_wish("Conduct a full port scan on IP 10.10.10.123.")

        # Create a mock for the chain
        mock_chain = MagicMock()
        error_message = "API rate limit exceeded"
        mock_chain.invoke.side_effect = Exception(error_message)

        # Act & Assert
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

                    # Expect CommandGenerationError to be raised
                    from wish_command_generation.exceptions import CommandGenerationError
                    with pytest.raises(CommandGenerationError) as excinfo:
                        # Create settings object
                        settings_obj = Settings()
                        generate_commands(state, settings_obj)

                    # Verify the error message
                    assert f"Command generation failed: {error_message}" in str(excinfo.value)

    def test_generate_commands_invalid_json(self):
        """Test that generate_commands raises CommandGenerationError for invalid JSON responses."""
        # Arrange
        state = GraphStateFactory.create_with_specific_wish("Conduct a full port scan on IP 10.10.10.123.")

        # Create a mock for the chain
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "This is not valid JSON"

        # Act & Assert
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

                    # Expect CommandGenerationError to be raised
                    from wish_command_generation.exceptions import CommandGenerationError
                    with pytest.raises(CommandGenerationError) as excinfo:
                        # Create settings object
                        settings_obj = Settings()
                        generate_commands(state, settings_obj)

                    # Verify the error message
                    assert "Invalid JSON format" in str(excinfo.value)
                    assert "This is not valid JSON" in str(excinfo.value)
