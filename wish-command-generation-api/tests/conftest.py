"""Test configuration for wish-command-generation-api."""

import os
import sys
from unittest.mock import patch

import pytest

# Mock API keys for unit tests
MOCK_OPENAI_API_KEY = "sk-test-key"
MOCK_LANGCHAIN_API_KEY = "ls-test-key"

@pytest.fixture(autouse=True)
def setup_test_env(request):
    """Set up test environment.
    
    Unit tests: Mock API keys
    Integration tests: Use actual API keys (skip if not available)
    """
    # Get test path
    test_path = request.node.fspath.strpath
    
    # For unit tests
    if "/unit/" in test_path:
        with patch.dict(os.environ, {
            "OPENAI_API_KEY": MOCK_OPENAI_API_KEY,
            "LANGCHAIN_API_KEY": MOCK_LANGCHAIN_API_KEY,
            "LANGCHAIN_TRACING_V2": "false"  # Disable tracing for unit tests
        }):
            yield
    # For integration tests
    else:
        # Check if actual API keys are set
        openai_key = os.environ.get("OPENAI_API_KEY")
        langchain_key = os.environ.get("LANGCHAIN_API_KEY")
        
        if openai_key in [None, "", "your-api-key-here"] or langchain_key in [None, "", "your-langsmith-api-key-here"]:
            pytest.fail("Integration tests require valid API keys")
        
        # Enable tracing for integration tests
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        
        yield
