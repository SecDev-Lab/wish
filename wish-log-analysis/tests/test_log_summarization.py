"""Tests for the log summarization node."""

import os
import tempfile
from unittest.mock import patch

import pytest
from wish_models.command_result import LogFiles, CommandResult

from wish_log_analysis.models import GraphState
from wish_log_analysis.nodes.log_summarization import summarize_log


class TestLogSummarization:
    """Tests for the log summarization node."""

    @patch("langchain_core.prompts.PromptTemplate")
    @patch("langchain_openai.ChatOpenAI")
    @patch("langchain_core.output_parsers.StrOutputParser")
    def test_summarize_log(self, mock_str_output_parser, mock_chat_openai, mock_prompt_template):
        """Test that the log summarization node works correctly."""
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
            mock_str_output_parser.invoke.return_value = "Hello, World!"

            # Call the function
            result = summarize_log(state)

            # Check that the mocks were called
            mock_prompt_template.from_template.assert_called_once()
            mock_chat_openai.assert_called_once()
            mock_str_output_parser.assert_called_once()

            # Check that the result is correct
            assert result.log_summary == "Hello, World!"
        finally:
            # Clean up the temporary files
            os.unlink(stdout_file.name)
            os.unlink(stderr_file.name)
