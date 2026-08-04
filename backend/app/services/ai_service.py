import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Optional

from app.core.config import settings
from app.core.exceptions import (
    AIServiceError,
    ModelNotFoundError,
    ProviderOverloadedError,
    ProviderRateLimitError,
)
from app.core.metrics import track_ai_request
from app.services.ai_model_router import ai_model_router

logger = logging.getLogger("omniai.ai_service")


def estimate_tokens(text: str) -> int:
    return len(text) // 4


async def retry_with_backoff(
    fn,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple = (ProviderOverloadedError, ProviderRateLimitError, ConnectionError, TimeoutError),
):
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                jitter = delay * 0.1 * (hash(str(time.time())) % 20 / 20)
                logger.warning(
                    "AI request failed, retrying",
                    extra={
                        "event": "ai_retry",
                        "attempt": attempt + 1,
                        "max_retries": max_retries,
                        "delay": round(delay + jitter, 2),
                        "error": str(e),
                    },
                )
                await asyncio.sleep(delay + jitter)
        except Exception as e:
            raise
    raise last_exception


class AIProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any] | AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def embeddings(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class OpenAIProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self._client = None
        self._aclient = None

    @property
    def name(self) -> str:
        return "openai"

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.OpenAI(api_key=self.api_key)
        return self._client

    def _get_aclient(self):
        if self._aclient is None:
            import openai
            self._aclient = openai.AsyncOpenAI(api_key=self.api_key, timeout=120.0, max_retries=0)
        return self._aclient

    async def chat_completion(self, messages, model=None, stream=False, temperature=0.7, max_tokens=4096):
        client = self._get_aclient()
        model = model or "gpt-4o"
        if stream:
            return self._stream_chat(client, model, messages, temperature, max_tokens)
        try:
            response = await client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            choice = response.choices[0].message
            return {
                "content": choice.content or "",
                "model": model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else 0,
                "tokens_completion": response.usage.completion_tokens if response.usage else 0,
            }
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                raise ProviderRateLimitError(provider="openai")
            if "overloaded" in error_str or "503" in error_str:
                raise ProviderOverloadedError(provider="openai")
            raise AIServiceError(detail=str(e), provider="openai")

    async def _stream_chat(self, client, model, messages, temperature, max_tokens):
        try:
            stream = await client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, stream=True
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                raise ProviderRateLimitError(provider="openai")
            if "overloaded" in error_str or "503" in error_str:
                raise ProviderOverloadedError(provider="openai")
            raise AIServiceError(detail=str(e), provider="openai")

    async def embeddings(self, texts, model=None):
        client = self._get_aclient()
        model = model or "text-embedding-3-small"
        try:
            response = await client.embeddings.create(model=model, input=texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="openai")


class AnthropicProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self._client = None

    @property
    def name(self) -> str:
        return "anthropic"

    def _get_client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key, timeout=120.0, max_retries=0)
        return self._client

    async def chat_completion(self, messages, model=None, stream=False, temperature=0.7, max_tokens=4096):
        client = self._get_client()
        model = model or "claude-3-5-sonnet-20241022"
        system = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append({"role": m["role"], "content": m["content"]})
        if stream:
            return self._stream_chat(client, model, system, chat_messages, temperature, max_tokens)
        try:
            response = await client.messages.create(
                model=model, system=system, messages=chat_messages, temperature=temperature, max_tokens=max_tokens
            )
            tokens = response.usage.input_tokens + response.usage.output_tokens if response.usage else 0
            return {
                "content": response.content[0].text if response.content else "",
                "model": model,
                "tokens_used": tokens,
                "tokens_prompt": response.usage.input_tokens if response.usage else 0,
                "tokens_completion": response.usage.output_tokens if response.usage else 0,
            }
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                raise ProviderRateLimitError(provider="anthropic")
            if "overloaded" in error_str or "529" in error_str:
                raise ProviderOverloadedError(provider="anthropic")
            raise AIServiceError(detail=str(e), provider="anthropic")

    async def _stream_chat(self, client, model, system, messages, temperature, max_tokens):
        try:
            async with client.messages.stream(
                model=model, system=system, messages=messages, temperature=temperature, max_tokens=max_tokens
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            error_str = str(e).lower()
            if "rate limit" in error_str:
                raise ProviderRateLimitError(provider="anthropic")
            if "overloaded" in error_str or "529" in error_str:
                raise ProviderOverloadedError(provider="anthropic")
            raise AIServiceError(detail=str(e), provider="anthropic")

    async def embeddings(self, texts, model=None):
        raise NotImplementedError("Anthropic does not provide embeddings API")


class OllamaProvider(AIProvider):
    def __init__(self):
        self.base_url = settings.ollama_base_url

    @property
    def name(self) -> str:
        return "ollama"

    async def chat_completion(self, messages, model=None, stream=False, temperature=0.7, max_tokens=4096):
        import httpx
        model = model or "llama3"
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if stream:
                    return self._stream_chat(client, url, payload)
                response = await client.post(url, json=payload, timeout=120)
                response.raise_for_status()
                data = response.json()
                return {
                    "content": data.get("message", {}).get("content", ""),
                    "model": model,
                    "tokens_used": 0,
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise ProviderRateLimitError(provider="ollama")
            if e.response.status_code >= 500:
                raise ProviderOverloadedError(provider="ollama")
            raise AIServiceError(detail=str(e), provider="ollama")
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="ollama")

    async def _stream_chat(self, client, url, payload):
        import httpx
        try:
            async with client.stream("POST", url, json=payload, timeout=120) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if data.get("done"):
                            break
                        yield data.get("message", {}).get("content", "")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise ProviderRateLimitError(provider="ollama")
            if e.response.status_code >= 500:
                raise ProviderOverloadedError(provider="ollama")
            raise AIServiceError(detail=str(e), provider="ollama")

    async def embeddings(self, texts, model=None):
        import httpx
        model = model or "nomic-embed-text"
        url = f"{self.base_url}/api/embed"
        payload = {"model": model, "input": texts}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload, timeout=60)
                response.raise_for_status()
                data = response.json()
                return data.get("embeddings", [])
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="ollama")


class DeepSeekProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self._client = None

    @property
    def name(self) -> str:
        return "deepseek"

    def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com",
                timeout=120.0,
                max_retries=0,
            )
        return self._client

    async def chat_completion(self, messages, model=None, stream=False, temperature=0.7, max_tokens=4096):
        client = self._get_client()
        model = model or "deepseek-chat"
        if stream:
            return self._stream_chat(client, model, messages, temperature, max_tokens)
        try:
            response = await client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            return {
                "content": response.choices[0].message.content or "",
                "model": model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else 0,
                "tokens_completion": response.usage.completion_tokens if response.usage else 0,
            }
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="deepseek")

    async def _stream_chat(self, client, model, messages, temperature, max_tokens):
        try:
            stream = await client.chat.completions.create(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens, stream=True
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="deepseek")

    async def embeddings(self, texts, model=None):
        raise NotImplementedError("DeepSeek does not provide embeddings API")


class MistralProvider(AIProvider):
    def __init__(self):
        self.api_key = settings.mistral_api_key
        self._client = None

    @property
    def name(self) -> str:
        return "mistral"

    def _get_client(self):
        if self._client is None:
            from mistralai import Mistral
            self._client = Mistral(api_key=self.api_key)
        return self._client

    async def chat_completion(self, messages, model=None, stream=False, temperature=0.7, max_tokens=4096):
        client = self._get_client()
        model = model or "mistral-large-latest"
        if stream:
            return self._stream_chat(client, model, messages, temperature, max_tokens)
        try:
            response = await client.chat.complete_async(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            choice = response.choices[0]
            return {
                "content": choice.message.content or "",
                "model": model,
                "tokens_used": response.usage.total_tokens if response.usage else 0,
                "tokens_prompt": response.usage.prompt_tokens if response.usage else 0,
                "tokens_completion": response.usage.completion_tokens if response.usage else 0,
            }
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="mistral")

    async def _stream_chat(self, client, model, messages, temperature, max_tokens):
        try:
            stream = await client.chat.stream_async(
                model=model, messages=messages, temperature=temperature, max_tokens=max_tokens
            )
            async for chunk in stream:
                if chunk.data.choices and chunk.data.choices[0].delta.content:
                    yield chunk.data.choices[0].delta.content
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="mistral")

    async def embeddings(self, texts, model=None):
        client = self._get_client()
        model = model or "mistral-embed"
        try:
            response = await client.embeddings.create_async(model=model, inputs=texts)
            return [item.embedding for item in response.data]
        except Exception as e:
            raise AIServiceError(detail=str(e), provider="mistral")


PROVIDER_PRIORITY = ["openai", "anthropic", "deepseek", "mistral", "ollama"]


class AIService:
    def __init__(self):
        self.providers: dict[str, AIProvider] = {}
        self._init_providers()

    def _init_providers(self):
        config_map = [
            ("openai", settings.openai_api_key, OpenAIProvider),
            ("anthropic", settings.anthropic_api_key, AnthropicProvider),
            ("deepseek", settings.deepseek_api_key, DeepSeekProvider),
            ("mistral", settings.mistral_api_key, MistralProvider),
        ]
        for name, api_key, provider_cls in config_map:
            if api_key:
                self.providers[name] = provider_cls()
        self.providers["ollama"] = OllamaProvider()

    def get_provider(self, preferred: Optional[str] = None) -> AIProvider:
        if preferred and preferred in self.providers:
            return self.providers[preferred]
        for name in PROVIDER_PRIORITY:
            if name in self.providers:
                return self.providers[name]
        raise AIServiceError(detail="No AI provider configured. Set at least one API key.")

    def _get_provider_fallback_chain(self, preferred: Optional[str] = None) -> list[AIProvider]:
        chain = []
        seen = set()
        if preferred and preferred in self.providers:
            chain.append(self.providers[preferred])
            seen.add(preferred)
        for name in PROVIDER_PRIORITY:
            if name in self.providers and name not in seen:
                chain.append(self.providers[name])
                seen.add(name)
        return chain

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider: Optional[str] = None,
        user_id: str = "",
        enable_metrics: bool = True,
        enable_retry: bool = True,
    ):
        providers = self._get_provider_fallback_chain(provider)
        if not providers:
            raise AIServiceError(detail="No AI provider configured. Set at least one API key.")

        last_error = None
        for p in providers:
            try:
                if enable_retry:
                    start = time.perf_counter()
                    result = await retry_with_backoff(
                        lambda pp=p: pp.chat_completion(
                            messages=messages, model=model, stream=stream,
                            temperature=temperature, max_tokens=max_tokens,
                        )
                    )
                else:
                    start = time.perf_counter()
                    result = await p.chat_completion(
                        messages=messages, model=model, stream=stream,
                        temperature=temperature, max_tokens=max_tokens,
                    )

                duration_ms = (time.perf_counter() - start) * 1000

                if enable_metrics and isinstance(result, dict):
                    track_ai_request(
                        model=result.get("model", model or "unknown"),
                        provider=p.name,
                        status="success",
                        duration_ms=duration_ms,
                        tokens_prompt=result.get("tokens_prompt", 0),
                        tokens_completion=result.get("tokens_completion", 0),
                    )

                return result

            except (ProviderOverloadedError, ProviderRateLimitError, ConnectionError, TimeoutError) as e:
                last_error = e
                logger.warning(
                    "AI provider failed, trying fallback",
                    extra={
                        "event": "ai_provider_fallback",
                        "provider": p.name,
                        "fallback_providers": [x.name for x in providers],
                        "error": str(e),
                    },
                )
                continue
            except AIServiceError as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                logger.error(
                    "Unexpected AI provider error",
                    extra={"event": "ai_provider_unexpected_error", "provider": p.name, "error": str(e)},
                )
                continue

        detail = f"All AI providers failed: {last_error}" if last_error else "All AI providers failed"
        raise AIServiceError(detail=detail)

    async def complete_stream(        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider: Optional[str] = None,
        user_id: str = "",
        enable_metrics: bool = True,
    ) -> AsyncGenerator[str, None]:
        providers = self._get_provider_fallback_chain(provider)
        if not providers:
            raise AIServiceError(detail="No AI provider configured. Set at least one API key.")

        last_error = None
        for p in providers:
            try:
                start = time.perf_counter()
                full_content = ""
                gen = await p.chat_completion(
                    messages=messages, model=model, stream=True,
                    temperature=temperature, max_tokens=max_tokens,
                )
                async for token in gen:
                    full_content += token
                    yield token

                duration_ms = (time.perf_counter() - start) * 1000
                if enable_metrics:
                    track_ai_request(
                        model=model or "unknown",
                        provider=p.name,
                        status="success",
                        duration_ms=duration_ms,
                    )
                return

            except (ProviderOverloadedError, ProviderRateLimitError, ConnectionError, TimeoutError) as e:
                last_error = e
                logger.warning(
                    "AI provider streaming failed, trying fallback",
                    extra={"event": "ai_stream_fallback", "provider": p.name, "error": str(e)},
                )
                continue
            except Exception as e:
                last_error = e
                logger.error(
                    "Unexpected AI streaming error",
                    extra={"event": "ai_stream_unexpected_error", "provider": p.name, "error": str(e)},
                )
                continue

        raise last_error or AIServiceError(detail="All AI providers failed for streaming")

    async def complete_with_guard(
        self,
        messages: list[dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        provider: Optional[str] = None,
        user_id: str = "",
        organization_id: str = "",
    ):
        from app.services.ai_security.prompt_guard import prompt_guard

        input_text = " ".join(m.get("content", "") for m in messages if m.get("content"))
        guard_result = await prompt_guard.check_input(
            text=input_text,
            user_id=user_id,
            organization_id=organization_id,
        )
        if not guard_result.allowed:
            raise AIServiceError(
                detail=f"Input blocked by security guard: {guard_result.blocked_reason}",
                provider="security_guard",
            )

        result = await self.complete(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            provider=provider,
            user_id=user_id,
        )

        if isinstance(result, dict) and result.get("content"):
            output_guard = await prompt_guard.check_output(
                text=result["content"],
                user_id=user_id,
            )
            if not output_guard.allowed:
                raise AIServiceError(
                    detail=f"Output blocked by security guard: {output_guard.blocked_reason}",
                    provider="security_guard",
                )
            if output_guard.validated_output:
                result["content"] = output_guard.validated_output

        return result

    async def embed(self, texts: list[str], model: Optional[str] = None):
        p = self.get_provider("openai")
        if p is None:
            p = self.get_provider()
        if p is None:
            raise AIServiceError(detail="No AI provider configured for embeddings")
        return await p.embeddings(texts, model)


ai_service = AIService()
