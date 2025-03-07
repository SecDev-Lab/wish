"""Tests for the command state classifier node."""

import os
import tempfile
from unittest.mock import patch

import pytest
from wish_models.command_result import LogFiles, CommandResult
from wish_models.command_result.command_state import CommandState

from wish_log_analysis.models import GraphState
from wish_log_analysis.nodes.command_state_classifier import classify_command_state


class TestCommandStateClassifier:
    """Tests for the command state classifier node."""

    @patch("langchain_core.prompts.PromptTemplate")
    @patch("langchain_openai.ChatOpenAI")
    @patch("langchain_core.output_parsers.StrOutputParser")
    def test_classify_command_state_success(self, mock_str_output_parser, mock_chat_openai, mock_prompt_template):
        """Test that the command state classifier node works correctly for success."""
        # Create temporary log files
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
            stdout_file.write("Hello, World!")
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
            stderr_file.write("")

        try:
            # Create a mock command result using the factory method
            log_files = LogFiles(
                stdout=stdout_file.name,
                stderr=stderr_file.name,
            )
            command_result = CommandResult.create(
                num=1,
                command="echo 'Hello, World!'",
                log_files=log_files,
            )
            command_result.exit_code = 0

            # Create a mock graph state
            state = GraphState(
                command_result=command_result,
            )

            # Set up the mocks
            mock_prompt_template.from_template.return_value = mock_prompt_template
            mock_prompt_template.__or__.return_value = mock_chat_openai
            mock_chat_openai.__or__.return_value = mock_str_output_parser
            mock_str_output_parser.invoke.return_value = "SUCCESS"

            # Call the function
            result = classify_command_state(state)

            # Check that the mocks were called
            mock_prompt_template.from_template.assert_called_once()
            mock_chat_openai.assert_called_once()
            mock_str_output_parser.assert_called_once()

            # Check that the result is correct
            assert result.command_state == CommandState.SUCCESS
        finally:
            # Clean up the temporary files
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)

    @patch("langchain_core.prompts.PromptTemplate")
    @patch("langchain_openai.ChatOpenAI")
    @patch("langchain_core.output_parsers.StrOutputParser")
    def test_classify_command_state_error(self, mock_str_output_parser, mock_chat_openai, mock_prompt_template):
        """Test that the command state classifier node works correctly for error."""
        # Create temporary log files
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stdout_file:
            stdout_file.write("")
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as stderr_file:
            stderr_file.write("Command not found: foo")

        try:
            # Create a mock command result using the factory method
            log_files = LogFiles(
                stdout=stdout_file.name,
                stderr=stderr_file.name,
            )
            command_result = CommandResult.create(
                num=1,
                command="foo",
                log_files=log_files,
            )
            command_result.exit_code = 127

            # Create a mock graph state
            state = GraphState(
                command_result=command_result,
            )

            # Set up the mocks
            mock_prompt_template.from_template.return_value = mock_prompt_template
            mock_prompt_template.__or__.return_value = mock_chat_openai
            mock_chat_openai.__or__.return_value = mock_str_output_parser
            mock_str_output_parser.invoke.return_value = "COMMAND_NOT_FOUND"

            # Call the function
            result = classify_command_state(state)

            # Check that the mocks were called
            mock_prompt_template.from_template.assert_called_once()
            mock_chat_openai.assert_called_once()
            mock_str_output_parser.assert_called_once()

            # Check that the result is correct
            assert result.command_state == CommandState.COMMAND_NOT_FOUND
        finally:
            # Clean up the temporary files
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)
