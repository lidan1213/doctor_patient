import importlib
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_adapter():
    """Return a mock adapter that can be configured per test."""
    adapter = MagicMock()
    adapter.name = "mock-adapter"
    adapter.generate = AsyncMock()
    adapter.generate_stream = AsyncMock()
    adapter.embed = AsyncMock()
    adapter.rerank = AsyncMock()
    return adapter


@pytest.fixture(autouse=True)
def patch_registry(mock_adapter):
    """Auto-patch get_adapter_registry() in all async_unit tests."""
    # Explicitly import modules first so patch() can find them
    modules = [
        "app.core.agent.intent",
        "app.core.rag.query_processor",
        "app.core.agent.response_gen",
        "app.core.agent.react_engine",
    ]
    for mod_path in modules:
        importlib.import_module(mod_path)

    with patch("app.core.agent.intent.get_adapter_registry", return_value=mock_adapter), \
         patch("app.core.rag.query_processor.get_adapter_registry", return_value=mock_adapter), \
         patch("app.core.agent.response_gen.get_adapter_registry", return_value=mock_adapter), \
         patch("app.core.agent.react_engine.get_adapter_registry", return_value=mock_adapter):
        yield mock_adapter
