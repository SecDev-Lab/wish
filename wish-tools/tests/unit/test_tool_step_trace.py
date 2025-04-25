"""
Unit tests for the Tool Step Trace module.

These tests mock the HTTP requests to avoid making actual API calls.
"""

from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph import StateGraph

from wish_tools.tool_step_trace import (
    StepTraceState,
    build_graph,
    encode_trace_message,
    main,
    post_step_trace,
)


class TestToolStepTrace:
    """Test cases for the Tool Step Trace module."""

    def test_encode_trace_message(self):
        """Test encoding trace message to Base64."""
        # Setup
        state = StepTraceState(
            run_id="test-run-id",
            trace_name="Test Trace",
            trace_message="Hello, World!"
        )

        # Call function
        result = encode_trace_message(state)

        # Verify result
        assert result.trace_message_base64 == "SGVsbG8sIFdvcmxkIQ=="
        assert result.run_id == state.run_id
        assert result.trace_name == state.trace_name
        assert result.trace_message == state.trace_message

    @patch("wish_tools.tool_step_trace.requests.post")
    def test_post_step_trace_success(self, mock_post):
        """Test posting step trace with success response."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Success"
        mock_post.return_value = mock_response

        # Setup state
        state = StepTraceState(
            run_id="test-run-id",
            trace_name="Test Trace",
            trace_message="Hello, World!",
            trace_message_base64="SGVsbG8sIFdvcmxkIQ=="
        )

        # Call function
        result = post_step_trace(state)

        # Verify result
        assert result.response_status_code == 200
        assert result.response_body == "Success"
        assert result.run_id == state.run_id
        assert result.trace_name == state.trace_name
        assert result.trace_message == state.trace_message
        assert result.trace_message_base64 == state.trace_message_base64

        # Verify mock was called with correct parameters
        mock_post.assert_called_once_with(
            "http://host.docker.internal:23456/api/addStepTrace",
            json={
                "run_id": "test-run-id",
                "trace_name": "Test Trace",
                "trace_message_base64": "SGVsbG8sIFdvcmxkIQ=="
            },
            headers={"Content-Type": "application/json"}
        )

    @patch("wish_tools.tool_step_trace.requests.post")
    def test_post_step_trace_error(self, mock_post):
        """Test posting step trace with error."""
        # Setup mock
        mock_post.side_effect = Exception("Connection error")

        # Setup state
        state = StepTraceState(
            run_id="test-run-id",
            trace_name="Test Trace",
            trace_message="Hello, World!",
            trace_message_base64="SGVsbG8sIFdvcmxkIQ=="
        )

        # Call function
        result = post_step_trace(state)

        # Verify result
        assert result.response_status_code == 599
        assert "Connection error" in result.response_body
        assert result.run_id == state.run_id
        assert result.trace_name == state.trace_name
        assert result.trace_message == state.trace_message
        assert result.trace_message_base64 == state.trace_message_base64

    def test_build_graph(self):
        """Test building the workflow graph."""
        # Call function
        graph = build_graph()

        # Verify result
        assert isinstance(graph, StateGraph)
        assert "encode_trace_message" in graph.nodes
        assert "post_step_trace" in graph.nodes

    @patch("wish_tools.tool_step_trace.build_graph")
    def test_main_success(self, mock_build_graph):
        """Test the main function with success path."""
        # Setup mock
        mock_graph = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.invoke.return_value = {
            "response_status_code": 200,
            "response_body": "Success"
        }
        mock_graph.compile.return_value = mock_workflow
        mock_build_graph.return_value = mock_graph

        # Call function
        result = main(
            run_id="test-run-id",
            trace_name="Test Trace",
            trace_message="Hello, World!"
        )

        # Verify result
        assert result["status_code"] == 200
        assert result["body"] == "Success"

        # Verify mocks were called
        mock_build_graph.assert_called_once()
        mock_graph.compile.assert_called_once()
        mock_workflow.invoke.assert_called_once()

    @patch("wish_tools.tool_step_trace.build_graph")
    def test_main_error(self, mock_build_graph):
        """Test the main function with error path."""
        # Setup mock
        mock_build_graph.side_effect = Exception("Test error")

        # Call function
        result = main(
            run_id="test-run-id",
            trace_name="Test Trace",
            trace_message="Hello, World!"
        )

        # Verify result
        assert result["status_code"] == 599
        assert "Test error" in result["body"]

        # Verify mock was called
        mock_build_graph.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-v", "test_tool_step_trace.py"])
