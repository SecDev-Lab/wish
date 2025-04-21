"""Test configuration for wish-command-generation-api."""

import os
from unittest.mock import patch

import pytest

# Mock API keys for unit tests
MOCK_OPENAI_API_KEY = "sk-test-key"
MOCK_LANGCHAIN_API_KEY = "ls-test-key"

@pytest.fixture(autouse=True)
def setup_test_env(request):
    """Set up test environment.
    
    Unit tests: Mock API keys
    Integration tests: Use actual API keys
    """
    # Get test path
    test_path = request.node.fspath.strpath

    # For unit tests only
    if "/unit/" in test_path:
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": MOCK_OPENAI_API_KEY,
            "LANGCHAIN_API_KEY": MOCK_LANGCHAIN_API_KEY,
            "LANGCHAIN_TRACING_V2": "false"  # Disable tracing for unit tests
        }):
            yield
    # For integration tests - no mocking, use actual environment variables
    else:
        yield
