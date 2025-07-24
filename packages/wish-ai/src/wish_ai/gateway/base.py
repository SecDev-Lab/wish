"""
Abstract base class for LLM gateway implementations.

This module defines the interface that all LLM gateway implementations
must follow for consistent integration across the wish system.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

logger = logging.getLogger(__name__)


class LLMGateway(ABC):
    """Abstract base class for LLM API integrations.

    This class defines the standard interface for connecting to and
    interacting with various LLM providers. All concrete implementations
    must implement these methods.
    """

    @abstractmethod
    async def generate_plan(self, prompt: str, context: dict[str, Any], stream: bool = False) -> str:
        """Generate a penetration testing plan based on the given prompt and context.

        Args:
            prompt: The formatted prompt to send to the LLM
            context: Additional context information (mode, state, etc.)
            stream: Whether to use streaming output (default: False)

        Returns:
            Generated plan as a string

        Raises:
            LLMGatewayError: If plan generation fails
        """
        pass

    @abstractmethod
    async def stream_response(self, prompt: str, context: dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream response chunks from the LLM.

        Args:
            prompt: The formatted prompt to send to the LLM
            context: Additional context information

        Yields:
            Response chunks as strings

        Raises:
            LLMGatewayError: If streaming fails
        """
        pass

    @abstractmethod
    async def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the given text.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count

        Raises:
            LLMGatewayError: If token estimation fails
        """
        pass

    @abstractmethod
    async def validate_api_key(self) -> bool:
        """Validate that the API key is working correctly.

        Returns:
            True if API key is valid, False otherwise

        Raises:
            LLMGatewayError: If validation check fails
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Get the name of the LLM model being used.

        Returns:
            Model name as string
        """
        pass

    @property
    @abstractmethod
    def max_tokens(self) -> int:
        """Get the maximum number of tokens supported by the model.

        Returns:
            Maximum token count
        """
        pass


class LLMGatewayError(Exception):
    """Base exception for LLM gateway operations."""

    def __init__(self, message: str, provider: str | None = None):
        super().__init__(message)
        self.provider = provider


class LLMAuthenticationError(LLMGatewayError):
    """Raised when authentication with LLM provider fails."""

    pass


class LLMRateLimitError(LLMGatewayError):
    """Raised when rate limit is exceeded."""

    pass


class LLMQuotaExceededError(LLMGatewayError):
    """Raised when usage quota is exceeded."""

    pass


class LLMConnectionError(LLMGatewayError):
    """Raised when connection to LLM provider fails."""

    pass
