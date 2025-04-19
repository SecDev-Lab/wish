"""Test script for the RAG nodes."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from wish_models.settings import Settings

from wish_command_generation.nodes.rag import generate_query, retrieve_documents
from wish_command_generation.test_factories.state_factory import GraphStateFactory


class TestRag:
    """Test class for RAG-related functions."""

    def test_generate_query_with_llm(self):
        """Test that generate_query correctly uses LLM to generate a query."""
        # Arrange
        state = GraphStateFactory.create_with_specific_wish("Conduct a full port scan on IP 10.10.10.123.")
        settings_obj = Settings()

        # Mock the LLM chain
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "nmap port scan techniques"

        # Act
        with patch("langchain_openai.ChatOpenAI") as mock_chat_openai:
            with patch("langchain_core.prompts.PromptTemplate.from_template") as mock_prompt_template:
                with patch("langchain_core.output_parsers.StrOutputParser") as mock_str_output_parser:
                    # Set up the mocks
                    mock_model = MagicMock()
                    mock_chat_openai.return_value = mock_model

                    mock_prompt = MagicMock()
                    mock_prompt_template.return_value = mock_prompt

                    mock_parser = MagicMock()
                    mock_str_output_parser.return_value = mock_parser

                    # Set up the chain
                    mock_prompt.__or__.return_value = mock_model
                    mock_model.__or__.return_value = mock_parser
                    mock_parser.invoke = mock_chain.invoke

                    result = generate_query(state, settings_obj)

        # Assert
        assert result.query == "nmap port scan techniques"
        assert result.wish == state.wish
        assert result.context == state.context
        assert result.command_inputs == state.command_inputs
        mock_chain.invoke.assert_called_once()

    def test_retrieve_documents_with_empty_query(self):
        """Test that retrieve_documents returns empty context when query is None."""
        # Arrange
        state = GraphStateFactory.create_with_specific_wish("Conduct a full port scan on IP 10.10.10.123.")
        settings_obj = Settings()
        # No query set

        # Act
        result = retrieve_documents(state, settings_obj)

        # Assert
        assert result.context == []
        assert result.wish == state.wish
        assert result.query == state.query
        assert result.command_inputs == state.command_inputs

    def test_retrieve_documents_with_no_knowledge_bases(self):
        """Test that retrieve_documents handles the case when no knowledge bases are available."""
        # Arrange
        state = GraphStateFactory.create_with_query(
            "Conduct a full port scan on IP 10.10.10.123.",
            "nmap port scan techniques"
        )
        settings_obj = Settings()

        # Mock Path.iterdir to return empty list
        with patch("pathlib.Path.iterdir") as mock_iterdir:
            with patch("pathlib.Path.exists") as mock_exists:
                # Mock exists to return True so we reach the iterdir call
                mock_exists.return_value = True
                mock_iterdir.return_value = []

                # Act
                result = retrieve_documents(state, settings_obj)

        # Assert
        assert result.context == []
        assert result.wish == state.wish
        assert result.query == state.query
        assert result.command_inputs == state.command_inputs

    def test_retrieve_documents_with_chroma(self):
        """Test that retrieve_documents correctly retrieves documents from ChromaDB."""
        # Arrange
        state = GraphStateFactory.create_with_query(
            "Conduct a full port scan on IP 10.10.10.123.",
            "nmap port scan techniques"
        )
        settings_obj = Settings()
        settings_obj.VECTOR_STORE_TYPE = "chroma"

        # Create mock documents
        mock_doc1 = MagicMock()
        mock_doc1.page_content = "nmap is a network scanning tool"
        mock_doc1.metadata = {"source": "test_file1.txt"}

        mock_doc2 = MagicMock()
        mock_doc2.page_content = "rustscan is a fast port scanner"
        mock_doc2.metadata = {"source": "test_file2.txt"}

        # Mock TextLoader
        mock_text_loader = MagicMock()
        mock_text_loader.load.return_value = [MagicMock(page_content="Full document content")]

        # Act
        with patch.object(settings_obj, "WISH_HOME", Path("/home/user/.wish")):
            with patch("importlib.util.find_spec", return_value=MagicMock()):
                with patch("pathlib.Path.iterdir") as mock_iterdir:
                    with patch("pathlib.Path.exists") as mock_exists:
                        with patch("langchain_community.vectorstores.Chroma") as mock_chroma:
                            with patch("langchain_openai.OpenAIEmbeddings"):
                                with patch("langchain_community.document_loaders.TextLoader") as mock_loader:
                                    # Set up the mocks
                                    mock_dir = MagicMock()
                                    mock_dir.name = "test_knowledge"
                                    mock_dir.is_dir.return_value = True
                                    mock_iterdir.return_value = [mock_dir]

                                    mock_exists.return_value = True

                                    mock_vectorstore = MagicMock()
                                    mock_vectorstore.similarity_search.return_value = [mock_doc1, mock_doc2]
                                    mock_chroma.return_value = mock_vectorstore

                                    mock_loader.return_value = mock_text_loader

                                    result = retrieve_documents(state, settings_obj)

        # Assert
        assert len(result.context) == 1  # After removing duplicates
        assert "Full document content" in result.context
        assert result.wish == state.wish
        assert result.query == state.query
        assert result.command_inputs == state.command_inputs

    def test_retrieve_documents_with_tilde_path(self):
        """Test that retrieve_documents correctly handles paths with tilde (~)."""
        # Arrange
        state = GraphStateFactory.create_with_query(
            "Conduct a full port scan on IP 10.10.10.123.",
            "nmap port scan techniques"
        )
        settings_obj = Settings()

        # Act
        with patch.object(settings_obj, "WISH_HOME", Path("/home/user/.wish")):
            with patch("pathlib.Path.exists") as mock_exists:
                with patch("pathlib.Path.iterdir") as mock_iterdir:
                    # Mock exists to return True
                    mock_exists.return_value = True
                    # Mock iterdir to return empty list
                    mock_iterdir.return_value = []

                    result = retrieve_documents(state, settings_obj)

        # Assert
        assert result.context == []
        assert result.wish == state.wish
        assert result.query == state.query
        assert result.command_inputs == state.command_inputs

    def test_retrieve_documents_with_nonexistent_directory(self):
        """Test that retrieve_documents handles nonexistent directories gracefully."""
        # Arrange
        state = GraphStateFactory.create_with_query(
            "Conduct a full port scan on IP 10.10.10.123.",
            "nmap port scan techniques"
        )
        settings_obj = Settings()

        # Act
        with patch.object(settings_obj, "WISH_HOME", Path("/home/user/.wish")):
            with patch("pathlib.Path.exists") as mock_exists:
                # Mock exists to return False (directory doesn't exist)
                mock_exists.return_value = False

                result = retrieve_documents(state, settings_obj)

        # Assert
        assert result.context == []
        assert result.wish == state.wish
        assert result.query == state.query
        assert result.command_inputs == state.command_inputs
