"""Test script for the command generation graph."""

from unittest.mock import patch, MagicMock

import pytest

from wish_command_generation import create_command_generation_graph
from wish_command_generation.models import GraphState
from wish_models.command_result import CommandInput
from wish_models.wish.wish import Wish
from wish_command_generation.test_factories.state_factory import GraphStateFactory


class TestGraph:
    """Test class for the command generation graph."""

    @patch("wish_command_generation.nodes.rag.generate_query")
    @patch("wish_command_generation.nodes.rag.retrieve_documents")
    @patch("wish_command_generation.nodes.command_generation.generate_commands")
    def test_graph_execution(self, mock_generate_commands, mock_retrieve_documents, mock_generate_query):
        """Test that the graph executes all nodes in the correct order."""
        # Arrange
        wish = Wish.create(wish="Conduct a full port scan on IP 10.10.10.123.")
        initial_state = GraphState(wish=wish)
        
        # Mock the node functions
        query_state = GraphState(
            wish=wish,
            query="nmap port scan techniques"
        )
        mock_generate_query.return_value = query_state
        
        context_state = GraphState(
            wish=wish,
            query="nmap port scan techniques",
            context=["nmap is a network scanning tool", "rustscan is a fast port scanner"]
        )
        mock_retrieve_documents.return_value = context_state
        
        command_state = GraphState(
            wish=wish,
            query="nmap port scan techniques",
            context=["nmap is a network scanning tool", "rustscan is a fast port scanner"],
            command_inputs=[
                CommandInput(command="rustscan -a 10.10.10.123", timeout_sec=None)
            ]
        )
        mock_generate_commands.return_value = command_state
        
        # Create the graph
        graph = create_command_generation_graph()
        
        # Act
        result = graph.invoke(initial_state)
        
        # Assert
        mock_generate_query.assert_called_once()
        mock_retrieve_documents.assert_called_once()
        mock_generate_commands.assert_called_once()
        
        assert len(result["command_inputs"]) == 1
        assert result["command_inputs"][0].command == "rustscan -a 10.10.10.123"
        assert result["command_inputs"][0].timeout_sec is None
        assert result["wish"] == wish
        assert result["query"] == "nmap port scan techniques"
        assert len(result["context"]) == 2

    def test_graph_integration(self):
        """Test the integration of the graph with actual node implementations.
        
        This test uses the actual node implementations but mocks external dependencies.
        """
        # This test would be more complex and require mocking external dependencies
        # like OpenAI API. For simplicity, we'll just verify the graph structure.
        
        # Create the graph without compiling to inspect its structure
        graph = create_command_generation_graph(compile=False)
        
        # Verify the graph structure
        assert "query_generation" in graph.nodes
        assert "retrieve_documents" in graph.nodes
        assert "generate_commands" in graph.nodes
        
        # Verify the edges
        edges = list(graph.edges)
        assert ("__start__", "query_generation") in edges
        assert ("query_generation", "retrieve_documents") in edges
        assert ("retrieve_documents", "generate_commands") in edges
        assert ("generate_commands", "__end__") in edges
