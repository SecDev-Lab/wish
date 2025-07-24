"""
OpenAI API implementation of the LLM gateway.

This module provides concrete implementation for connecting to OpenAI's
API for plan generation and streaming responses.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from typing import Any

import tiktoken
from openai import AsyncOpenAI
from wish_core.config import get_api_key, get_llm_config

from .base import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMGateway,
    LLMGatewayError,
    LLMQuotaExceededError,
    LLMRateLimitError,
)

logger = logging.getLogger(__name__)


class OpenAIGateway(LLMGateway):
    _client: AsyncOpenAI | None
    """OpenAI API implementation of the LLM gateway.

    This class provides integration with OpenAI's GPT models for
    penetration testing plan generation and assistance.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        timeout: float | None = None,
    ):
        """Initialize the OpenAI gateway.

        Args:
            api_key: OpenAI API key (defaults to config/env hierarchy)
            model: Model name to use (defaults to config)
            max_tokens: Maximum tokens for responses (defaults to config)
            temperature: Response creativity (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        # Get configuration from wish-core
        llm_config = get_llm_config()

        # Use provided values or fall back to configuration hierarchy
        # Following fail-fast principle: immediately raise exception if no API key
        self.api_key = api_key or get_api_key()
        if not self.api_key:
            raise LLMAuthenticationError(
                "OpenAI API key not provided. Set OPENAI_API_KEY environment variable "
                "or configure in ~/.wish/config.toml",
                provider="openai",
            )

        # Log API key info (masked for security)
        masked_key = f"{self.api_key[:8]}...{self.api_key[-4:]}" if len(self.api_key) > 12 else "***"
        logger.info(f"Using OpenAI API key: {masked_key}")

        self._model = model or llm_config.model
        self._max_tokens = max_tokens or llm_config.max_tokens
        self.temperature = temperature or llm_config.temperature
        self.timeout = timeout or llm_config.timeout

        # Initialize client and tokenizer
        logger.debug(f"Initializing AsyncOpenAI client with timeout: {self.timeout}s")
        try:
            self._client = AsyncOpenAI(api_key=self.api_key, timeout=self.timeout)
            logger.debug("AsyncOpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AsyncOpenAI client: {e}")
            raise

        try:
            self._tokenizer = tiktoken.encoding_for_model(self._model)
        except KeyError:
            # Fallback for newer models
            logger.debug(f"Model {self._model} not found in tiktoken, using cl100k_base encoding")
            self._tokenizer = tiktoken.get_encoding("cl100k_base")

        logger.info(f"Initialized OpenAI gateway with model: {self._model}, timeout: {self.timeout}s")

    @property
    def model_name(self) -> str:
        """Get the name of the OpenAI model being used."""
        return self._model

    @property
    def max_tokens(self) -> int:
        """Get the maximum number of tokens supported."""
        return self._max_tokens

    async def generate_plan(self, prompt: str, context: dict[str, Any], stream: bool = False) -> str:
        """Generate a penetration testing plan using OpenAI.

        Args:
            prompt: The formatted prompt to send to OpenAI
            context: Additional context information
            stream: Whether to use streaming (not used in this method)

        Returns:
            Generated plan as a string

        Raises:
            LLMGatewayError: If plan generation fails
        """
        try:
            logger.info(f"Starting plan generation with model: {self._model}, timeout: {self.timeout}s")
            logger.debug(f"Prompt length: {len(prompt)} characters")

            # Log that we're about to make the API call
            logger.debug("Making OpenAI API call...")
            start_time = asyncio.get_event_loop().time()

            # Use asyncio.wait_for to enforce timeout explicitly
            assert self._client is not None
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=min(self._max_tokens, 4000),  # Reserve tokens for response
                    stream=False,
                ),
                timeout=self.timeout,
            )

            elapsed_time = asyncio.get_event_loop().time() - start_time
            logger.info(f"OpenAI API call completed in {elapsed_time:.2f} seconds")

            if not response.choices:
                logger.error("No response choices returned from OpenAI")
                raise LLMGatewayError("No response choices returned from OpenAI", provider="openai")

            content = response.choices[0].message.content
            if not content:
                logger.error("Empty response content from OpenAI")
                raise LLMGatewayError("Empty response content from OpenAI", provider="openai")

            logger.info(f"Successfully generated plan with {len(content)} characters")
            logger.debug(f"First 200 chars of response: {content[:200]}...")
            return content.strip()

        except TimeoutError as e:
            logger.error(f"OpenAI API request timed out after {self.timeout} seconds")
            raise LLMConnectionError(
                f"OpenAI API request timed out after {self.timeout} seconds. "
                "Consider increasing the timeout in configuration or check your network connection.",
                provider="openai",
            ) from e
        except Exception as e:
            logger.error(f"Error during OpenAI API call: {type(e).__name__}: {str(e)}")
            await self._handle_openai_error(e)
            # This line should never be reached as _handle_openai_error always raises
            raise LLMGatewayError(f"Unexpected error: {e}", provider="openai") from e

    async def stream_response(self, prompt: str, context: dict[str, Any]) -> AsyncGenerator[str, None]:  # type: ignore[override]
        """Stream response chunks from OpenAI.

        Args:
            prompt: The formatted prompt to send to OpenAI
            context: Additional context information

        Yields:
            Response chunks as strings

        Raises:
            LLMGatewayError: If streaming fails
        """
        try:
            logger.debug(f"Starting streaming response with model: {self._model}, timeout: {self.timeout}s")

            assert self._client is not None
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    max_tokens=min(self._max_tokens, 4000),
                    stream=True,
                ),
                timeout=self.timeout,
            )

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except TimeoutError as e:
            raise LLMConnectionError(
                f"OpenAI API streaming request timed out after {self.timeout} seconds. "
                "Consider increasing the timeout in configuration.",
                provider="openai",
            ) from e
        except Exception as e:
            await self._handle_openai_error(e)

    async def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in the given text using tiktoken.

        Args:
            text: Text to estimate tokens for

        Returns:
            Estimated token count
        """
        try:
            tokens = self._tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Failed to estimate tokens: {e}")
            # Fallback estimation: roughly 4 characters per token
            return len(text) // 4

    async def validate_api_key(self) -> bool:
        """Validate that the OpenAI API key is working correctly.

        Returns:
            True if API key is valid, False otherwise

        Raises:
            LLMGatewayError: If validation check fails
        """
        try:
            logger.debug("Validating OpenAI API key")

            # Use a minimal request to test API key
            assert self._client is not None
            response = await self._client.chat.completions.create(
                model=self._model, messages=[{"role": "user", "content": "Test"}], max_tokens=1, temperature=0
            )

            return bool(response.choices)

        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False

    async def _handle_openai_error(self, error: Exception) -> None:
        """Handle OpenAI-specific errors and convert to appropriate exceptions.

        Args:
            error: The original exception from OpenAI

        Raises:
            Appropriate LLMGatewayError subclass
        """
        error_message = str(error)

        # Check for specific OpenAI error types
        if "authentication" in error_message.lower() or "api_key" in error_message.lower():
            raise LLMAuthenticationError(f"OpenAI authentication failed: {error_message}", provider="openai")

        if "rate_limit" in error_message.lower() or "rate limit" in error_message.lower():
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {error_message}", provider="openai")

        if "quota" in error_message.lower() or "billing" in error_message.lower():
            raise LLMQuotaExceededError(f"OpenAI quota exceeded: {error_message}", provider="openai")

        if "connection" in error_message.lower() or "timeout" in error_message.lower():
            raise LLMConnectionError(f"OpenAI connection failed: {error_message}", provider="openai")

        # Generic error
        raise LLMGatewayError(f"OpenAI API error: {error_message}", provider="openai")

    async def close(self) -> None:
        """Close the OpenAI client and cleanup resources."""
        if hasattr(self, "_client"):
            try:
                # OpenAI's AsyncOpenAI client uses httpx internally
                # We need to close the underlying HTTP client
                if self._client and hasattr(self._client, "_client"):
                    await self._client._client.aclose()
                elif self._client and hasattr(self._client, "close"):
                    await self._client.close()
            except Exception as e:
                logger.debug(f"Error closing OpenAI client: {e}")
            finally:
                self._client = None
