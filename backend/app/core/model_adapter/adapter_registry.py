import logging
from typing import AsyncGenerator

from app.config import settings
from app.core.model_adapter.base import BaseLLMAdapter
from app.core.model_adapter.dashscope_adapter import DashScopeAdapter
from app.core.model_adapter.ollama_adapter import OllamaAdapter

logger = logging.getLogger(__name__)


class AllAdaptersFailedError(Exception):
    pass


class AdapterRegistry:
    """Priority-chain adapter registry with automatic fallback.

    inference: dashscope → ollama
    embedding: ollama only (always local)
    reranker: ollama → dashscope
    """

    def __init__(self):
        dashscope = DashScopeAdapter()
        ollama_chat = OllamaAdapter(model="qwen3:14b")
        ollama_embed = OllamaAdapter(model="qwen3-embedding")

        self._chains: dict[str, list[BaseLLMAdapter]] = {
            "inference": [dashscope, ollama_chat],
            "embedding": [ollama_embed],
            "reranker": [ollama_chat, dashscope],
        }

    def _chain(self, purpose: str) -> list[BaseLLMAdapter]:
        if purpose == "inference":
            if settings.inference_backend == "ollama":
                return [self._chains["inference"][1]]
            elif settings.inference_backend == "dashscope":
                return [self._chains["inference"][0]]
        elif purpose == "reranker":
            if settings.reranker_backend == "dashscope":
                return [self._chains["reranker"][1]]
        return self._chains.get(purpose, self._chains["inference"])

    async def generate(
        self, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 2048
    ) -> str:
        for adapter in self._chain("inference"):
            try:
                return await adapter.generate(messages, temperature, max_tokens)
            except Exception as e:
                logger.warning(f"Adapter {adapter.name} failed: {e}, trying next")
        raise AllAdaptersFailedError("All inference adapters failed")

    async def generate_stream(
        self, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        last_error = None
        for adapter in self._chain("inference"):
            try:
                async for chunk in adapter.generate_stream(messages, temperature, max_tokens):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Adapter {adapter.name} stream failed: {e}, trying next")
                last_error = e
        raise AllAdaptersFailedError(f"All inference adapters failed for streaming: {last_error}")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        for adapter in self._chain("embedding"):
            try:
                return await adapter.embed(texts)
            except Exception as e:
                logger.warning(f"Embedding adapter {adapter.name} failed: {e}")
        raise AllAdaptersFailedError("All embedding adapters failed")

    async def rerank(self, query: str, documents: list[str], top_n: int = 5) -> list[dict]:
        for adapter in self._chain("reranker"):
            try:
                return await adapter.rerank(query, documents, top_n)
            except Exception as e:
                logger.warning(f"Reranker adapter {adapter.name} failed: {e}")
        raise AllAdaptersFailedError("All reranker adapters failed")


_adapter_registry: AdapterRegistry | None = None


def get_adapter_registry() -> AdapterRegistry:
    global _adapter_registry
    if _adapter_registry is None:
        _adapter_registry = AdapterRegistry()
    return _adapter_registry
