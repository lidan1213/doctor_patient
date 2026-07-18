import base64
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.multimodal.doubao_client import DoubaoClient, get_doubao_client


class TestDoubaoClientInit:
    def test_uses_settings_by_default(self):
        client = DoubaoClient(api_key="sk-test", app_id="app-1", access_token="tok-1")
        assert client.api_key == "sk-test"
        assert client.app_id == "app-1"
        assert client.access_token == "tok-1"

    def test_default_models(self):
        client = DoubaoClient(api_key="sk-test", app_id="app-1", access_token="tok-1")
        assert client.vision_model == "doubao-seed-evolving"

    def test_auth_headers_no_app_id(self):
        client = DoubaoClient(api_key="sk-test", app_id="app-1", access_token="tok-1")
        headers = client._ark_headers
        assert headers["Authorization"] == "Bearer sk-test"

    def test_voice_headers(self):
        client = DoubaoClient(api_key="sk-test", app_id="app-1", access_token="tok-1")
        headers = client._voice_headers
        assert headers["X-Api-App-Key"] == "app-1"
        assert headers["X-Api-Access-Key"] == "tok-1"


class TestDoubaoClientTTS:
    @pytest.mark.asyncio
    async def test_text_to_success(self):
        audio_b64 = base64.b64encode(b"fake-mp3-data").decode()
        mock_json = {"audio": audio_b64, "duration": 1.5}

        client = DoubaoClient(api_key="sk-test", app_id="app-1", access_token="tok-1", tts_model="seed-audio-1.0")

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.return_value = mock_json
            mock_client.post.return_value = mock_resp
            mock_cls.return_value = mock_client

            result = await client.text_to_speech("你好")

        assert result == b"fake-mp3-data"
        call_args = mock_client.post.call_args
        assert "api/v3/tts/create" in call_args.args[0]
        payload = call_args.kwargs["json"]
        assert payload["model"] == "seed-audio-1.0"
        assert payload["text_prompt"] == "你好"

    @pytest.mark.asyncio
    async def test_text_to_speech_downloads_from_url(self):
        mock_json = {"url": "https://example.com/audio.mp3", "duration": 1.5}

        client = DoubaoClient(api_key="sk-test", app_id="app-1", access_token="tok-1", tts_model="seed-audio-1.0")

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            # First response (create)
            resp1 = MagicMock()
            resp1.raise_for_status.return_value = None
            resp1.json.return_value = mock_json
            # Second response (download)
            resp2 = MagicMock()
            resp2.raise_for_status.return_value = None
            resp2.content = b"downloaded-audio"
            mock_client.post.return_value = resp1
            mock_client.get.return_value = resp2
            mock_cls.return_value = mock_client

            result = await client.text_to_speech("你好")

        assert result == b"downloaded-audio"


class TestDoubaoClientOCR:
    @pytest.mark.asyncio
    async def test_ocr_image_sends_b64_image(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "血常规 白细胞: 5.2×10⁹/L"}}]
        }

        client = DoubaoClient(api_key="sk-test", app_id="app-1", access_token="tok-1")
        img = b"\xff\xd8\xff\xe0"

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value = mock_client
            mock_client.post.return_value = mock_resp
            mock_client_cls.return_value = mock_client

            result = await client.ocr_image(img)

        assert "血常规" in result
        call_args = mock_client.post.call_args
        payload = call_args.kwargs["json"]
        assert payload["model"] == "doubao-seed-evolving"
        messages = payload["messages"]
        user_content = messages[0]["content"]
        assert user_content[0]["type"] == "image_url"
        assert "base64" in user_content[0]["image_url"]["url"]


class TestGetDoubaoClient:
    def test_returns_singleton(self):
        from app.core.multimodal import doubao_client as mod

        original = mod._doubao_client
        mod._doubao_client = None
        try:
            c1 = get_doubao_client()
            c2 = get_doubao_client()
            assert c1 is c2
        finally:
            mod._doubao_client = original
