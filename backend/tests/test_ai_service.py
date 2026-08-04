import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import AIServiceError, ProviderOverloadedError, ProviderRateLimitError
from app.services.ai_service import AIService, OpenAIProvider, AnthropicProvider, retry_with_backoff


@pytest.mark.asyncio
class TestAIProvider:
    async def test_openai_provider_complete(self):
        provider = OpenAIProvider()
        provider._get_aclient = MagicMock()
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.usage.total_tokens = 10
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 5
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        provider._get_aclient = MagicMock(return_value=mock_client)

        result = await provider.chat_completion(
            messages=[{"role": "user", "content": "Say hello"}],
            model="gpt-4o-mini",
        )
        assert result["content"] == "Hello!"
        assert result["model"] == "gpt-4o-mini"
        assert result["tokens_used"] == 10

    async def test_openai_provider_rate_limit(self):
        provider = OpenAIProvider()
        provider._get_aclient = MagicMock()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Rate limit exceeded")
        )
        provider._get_aclient = MagicMock(return_value=mock_client)

        with pytest.raises(ProviderRateLimitError):
            await provider.chat_completion(
                messages=[{"role": "user", "content": "test"}],
            )

    async def test_openai_provider_overloaded(self):
        provider = OpenAIProvider()
        provider._get_aclient = MagicMock()
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("overloaded")
        )
        provider._get_aclient = MagicMock(return_value=mock_client)

        with pytest.raises(ProviderOverloadedError):
            await provider.chat_completion(
                messages=[{"role": "user", "content": "test"}],
            )


@pytest.mark.asyncio
class TestAIService:
    @pytest.fixture
    def service(self):
        svc = AIService()
        svc.providers = {}
        return svc

    async def test_no_provider_raises_error(self, service):
        with pytest.raises(AIServiceError, match="No AI provider configured"):
            await service.complete(messages=[{"role": "user", "content": "test"}])

    async def test_get_provider_fallback_chain(self, service):
        mock_openai = AsyncMock(spec=OpenAIProvider)
        mock_openai.name = "openai"
        mock_anthropic = AsyncMock(spec=AnthropicProvider)
        mock_anthropic.name = "anthropic"
        service.providers = {"openai": mock_openai, "anthropic": mock_anthropic}

        providers = service._get_provider_fallback_chain("anthropic")
        assert providers[0].name == "anthropic"
        assert providers[1].name == "openai"

    async def test_complete_fallback_on_overload(self, service):
        mock_openai = AsyncMock(spec=OpenAIProvider)
        mock_openai.name = "openai"
        mock_openai.chat_completion = AsyncMock(side_effect=ProviderOverloadedError("openai"))
        mock_anthropic = AsyncMock(spec=AnthropicProvider)
        mock_anthropic.name = "anthropic"
        mock_anthropic.chat_completion = AsyncMock(return_value={
            "content": "fallback response", "model": "claude", "tokens_used": 5,
            "tokens_prompt": 2, "tokens_completion": 3,
        })
        service.providers = {"openai": mock_openai, "anthropic": mock_anthropic}

        with patch("app.services.ai_service.track_ai_request"):
            result = await service.complete(
                messages=[{"role": "user", "content": "test"}],
                enable_retry=False,
            )
        assert result["content"] == "fallback response"

    async def test_complete_fallback_all_fail(self, service):
        mock_openai = AsyncMock(spec=OpenAIProvider)
        mock_openai.name = "openai"
        mock_openai.chat_completion = AsyncMock(side_effect=ProviderOverloadedError("openai"))
        service.providers = {"openai": mock_openai}

        with pytest.raises(AIServiceError, match="All AI providers failed"):
            await service.complete(
                messages=[{"role": "user", "content": "test"}],
                enable_retry=False,
            )


@pytest.mark.asyncio
class TestRetryWithBackoff:
    async def test_retry_success_after_failure(self):
        call_count = 0

        async def failing_fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ProviderOverloadedError("test")
            return "success"

        result = await retry_with_backoff(
            failing_fn, max_retries=3, base_delay=0.01
        )
        assert result == "success"
        assert call_count == 3

    async def test_retry_exhausted(self):
        async def always_fails():
            raise ProviderOverloadedError("test")

        with pytest.raises(ProviderOverloadedError):
            await retry_with_backoff(
                always_fails, max_retries=2, base_delay=0.01
            )

    async def test_retry_non_retryable_exception(self):
        async def fails():
            raise ValueError("non-retryable")

        with pytest.raises(ValueError):
            await retry_with_backoff(
                fails, max_retries=3, base_delay=0.01
            )


class TestEstimateTokens:
    def test_estimate_tokens(self):
        from app.services.ai_service import estimate_tokens
        assert estimate_tokens("hello world") == 2
        assert estimate_tokens("") == 0
        assert estimate_tokens("a" * 100) == 25
