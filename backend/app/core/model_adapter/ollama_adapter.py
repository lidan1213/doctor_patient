import json
import logging
from typing import AsyncGenerator

import httpx
from app.config import settings
from app.core.model_adapter.base import BaseLLMAdapter

logger = logging.getLogger(__name__)


class OllamaAdapter(BaseLLMAdapter):
    """Ollama local model adapter (Qwen3 series)."""

    def __init__(self, model: str = "qwen3:14b"):
        self._model = model

    @property
    def name(self) -> str:
        return "ollama"

    async def generate(self, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 2048) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.ollama_host}/api/chat",
                json={
                    "model": self._model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": temperature, "num_predict": max_tokens, "enable_thinking": False},
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    async def generate_stream(
        self, messages: list[dict[str, str]], temperature: float = 0.7, max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{settings.ollama_host}/api/chat",
                json={
                    "model": self._model,
                    "messages": messages,
                    "stream": True,
                    "options": {"temperature": temperature, "num_predict": max_tokens, "enable_thinking": False},
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    try:
                        data = json.loads(line)
                        content = data.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

    async def embed(self, texts: list[str]) -> list[list[float]]:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.ollama_host}/api/embed",
                json={"model": self._model, "input": texts},
            )
            resp.raise_for_status()
            return resp.json()["embeddings"]

    async def rerank(self, query: str, documents: list[str], top_n: int = 5) -> list[dict]:
        """Use Ollama-hosted Qwen3-Reranker via a chat-based scoring approach."""
        scored: list[dict] = []
        async with httpx.AsyncClient(timeout=120) as client:
            for idx, doc in enumerate(documents):
                resp = await client.post(
                    f"{settings.ollama_host}/api/chat",
                    json={
                        "model": self._model,
                        "messages": [
                            {"role": "system", "content": "Judge relevance. Output only a number 0-1."},
                            {"role": "user", "content": f"Query: {query}\nDocument: {doc}\nRelevance score (0-1):"},
                        ],
                        "stream": False,
                        "options": {"temperature": 0, "num_predict": 50, "enable_thinking": False},
                    },
                )
                resp.raise_for_status()
                try:
                    score = float(resp.json()["message"]["content"].strip())
                except (ValueError, KeyError):
                    score = 0.0
                scored.append({"index": idx, "relevance_score": score, "document": doc})
        scored.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored[:top_n]
