"""
Tests for LLM gateway implementations.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from wish_ai.gateway import LLMGateway, OpenAIGateway
from wish_ai.gateway.base import LLMAuthenticationError, LLMConnectionError, LLMGatewayError, LLMRateLimitError


class TestLLMGateway:
    """Tests for the abstract LLMGateway class."""

    def test_gateway_is_abstract(self):
        """Test that LLMGateway cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMGateway()


class TestOpenAIGateway:
    """Tests for the OpenAI gateway implementation."""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        gateway = OpenAIGateway(api_key="test-key", model="gpt-4o")
        assert gateway.api_key == "test-key"
        assert gateway.model_name == "gpt-4o"
        assert gateway.max_tokens == 8000

    def test_init_without_api_key_raises_error(self):
        """Test that missing API key raises authentication error."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("wish_ai.gateway.openai.get_api_key", return_value=None):
                with pytest.raises(LLMAuthenticationError):
                    OpenAIGateway()

    @patch.dict("os.environ", {"OPENAI_API_KEY": "env-test-key"})
    def test_init_from_env_var(self):
        """Test initialization from environment variable."""
        gateway = OpenAIGateway()
        assert gateway.api_key == "env-test-key"

    @pytest.mark.asyncio
    async def test_estimate_tokens(self):
        """Test token estimation."""
        gateway = OpenAIGateway(api_key="test-key")

        # Test short text
        tokens = await gateway.estimate_tokens("Hello world")
        assert isinstance(tokens, int)
        assert tokens > 0

        # Test longer text should have more tokens
        long_text = "This is a much longer text that should have more tokens than the short one."
        long_tokens = await gateway.estimate_tokens(long_text)
        assert long_tokens > tokens

    @pytest.mark.asyncio
    async def test_generate_plan_success(self):
        """Test successful plan generation."""
        gateway = OpenAIGateway(api_key="test-key")

        # Mock the OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test plan response"

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            result = await gateway.generate_plan(prompt="Test prompt", context={"mode": "recon"})

            assert result == "Test plan response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_plan_empty_response(self):
        """Test handling of empty response."""
        gateway = OpenAIGateway(api_key="test-key")

        # Mock empty response
        mock_response = Mock()
        mock_response.choices = []

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            with pytest.raises(LLMGatewayError, match="No response choices"):
                await gateway.generate_plan("test", {})

    @pytest.mark.asyncio
    async def test_stream_response(self):
        """Test streaming response."""
        gateway = OpenAIGateway(api_key="test-key")

        # Mock streaming response
        mock_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Hello "))]),
            Mock(choices=[Mock(delta=Mock(content="world!"))]),
            Mock(choices=[Mock(delta=Mock(content=None))]),  # End of stream
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())

            result_chunks = []
            async for chunk in gateway.stream_response("test", {}):
                result_chunks.append(chunk)

            assert result_chunks == ["Hello ", "world!"]

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self):
        """Test successful API key validation."""
        gateway = OpenAIGateway(api_key="test-key")

        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            result = await gateway.validate_api_key()
            assert result is True

    @pytest.mark.asyncio
    async def test_validate_api_key_failure(self):
        """Test API key validation failure."""
        gateway = OpenAIGateway(api_key="test-key")

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Auth failed"))

            result = await gateway.validate_api_key()
            assert result is False

    @pytest.mark.asyncio
    async def test_error_handling_authentication(self):
        """Test authentication error handling."""
        gateway = OpenAIGateway(api_key="test-key")

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("authentication failed"))

            with pytest.raises(LLMAuthenticationError):
                await gateway.generate_plan("test", {})

    @pytest.mark.asyncio
    async def test_error_handling_rate_limit(self):
        """Test rate limit error handling."""
        gateway = OpenAIGateway(api_key="test-key")

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("rate limit exceeded"))

            with pytest.raises(LLMRateLimitError):
                await gateway.generate_plan("test", {})

    @pytest.mark.asyncio
    async def test_error_handling_connection(self):
        """Test connection error handling."""
        gateway = OpenAIGateway(api_key="test-key")

        with patch.object(gateway, "_client") as mock_client:
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("connection timeout"))

            with pytest.raises(LLMConnectionError):
                await gateway.generate_plan("test", {})


@pytest.fixture
def mock_openai_gateway():
    """Fixture providing a mocked OpenAI gateway."""
    gateway = OpenAIGateway(api_key="test-key")

    # Mock the client to avoid actual API calls
    with patch.object(gateway, "_client") as mock_client:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Mocked response"

        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        yield gateway
