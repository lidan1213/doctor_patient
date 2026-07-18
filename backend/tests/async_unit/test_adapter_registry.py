import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.model_adapter.adapter_registry import AdapterRegistry, AllAdaptersFailedError


@pytest.fixture
def mock_dashscope():
    adapter = MagicMock()
    adapter.name = "dashscope"
    adapter.generate = AsyncMock(return_value="dashscope result")
    adapter.generate_stream = MagicMock()
    adapter.embed = AsyncMock()
    adapter.rerank = AsyncMock()
    return adapter


@pytest.fixture
def mock_ollama():
    adapter = MagicMock()
    adapter.name = "ollama"
    adapter.generate = AsyncMock(return_value="ollama result")
    adapter.generate_stream = MagicMock()
    adapter.embed = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    adapter.rerank = AsyncMock(return_value=[{"index": 0, "relevance_score": 0.9}])
    return adapter


@pytest.fixture
def registry_with_mocks(mock_dashscope, mock_ollama):
    registry = AdapterRegistry()
    registry._chains = {
        "inference": [mock_dashscope, mock_ollama],
        "embedding": [mock_ollama],
        "reranker": [mock_ollama, mock_dashscope],
    }
    return registry


class TestAdapterRegistryGenerate:
    async def test_first_adapter_succeeds(self, registry_with_mocks, mock_dashscope):
        result = await registry_with_mocks.generate([{"role": "user", "content": "test"}])
        assert result == "dashscope result"
        mock_dashscope.generate.assert_awaited_once()

    async def test_fallback_on_first_failure(self, registry_with_mocks, mock_dashscope, mock_ollama):
        mock_dashscope.generate.side_effect = RuntimeError("API down")

        result = await registry_with_mocks.generate([{"role": "user", "content": "test"}])
        assert result == "ollama result"
        mock_dashscope.generate.assert_awaited_once()
        mock_ollama.generate.assert_awaited_once()

    async def test_all_failed_raises_error(self, registry_with_mocks, mock_dashscope, mock_ollama):
        mock_dashscope.generate.side_effect = RuntimeError("dashscope down")
        mock_ollama.generate.side_effect = RuntimeError("ollama down")

        with pytest.raises(AllAdaptersFailedError):
            await registry_with_mocks.generate([{"role": "user", "content": "test"}])


class TestAdapterRegistryStream:
    async def test_stream_fallback(self, registry_with_mocks, mock_dashscope, mock_ollama):
        mock_dashscope.generate_stream.side_effect = RuntimeError("stream failed")

        async def ollama_stream(*args, **kwargs):
            yield "chunk1"
            yield "chunk2"

        mock_ollama.generate_stream = ollama_stream

        chunks = []
        async for chunk in registry_with_mocks.generate_stream([{"role": "user", "content": "t"}]):
            chunks.append(chunk)

        assert chunks == ["chunk1", "chunk2"]


class TestAdapterRegistryEmbed:
    async def test_embed_uses_embedding_chain(self, registry_with_mocks, mock_ollama):
        result = await registry_with_mocks.embed(["test text"])
        assert result == [[0.1, 0.2, 0.3]]
        mock_ollama.embed.assert_awaited_once()


class TestAdapterRegistryRerank:
    async def test_rerank_uses_reranker_chain(self, registry_with_mocks, mock_ollama, monkeypatch):
        monkeypatch.setattr("app.core.model_adapter.adapter_registry.settings.reranker_backend", "ollama", raising=False)
        result = await registry_with_mocks.rerank("query", ["doc1"], top_n=3)
        assert result == [{"index": 0, "relevance_score": 0.9}]
        mock_ollama.rerank.assert_awaited_once_with("query", ["doc1"], 3)
