import asyncio
import base64
import json
import logging
import uuid
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
VOICE_BASE_URL = "https://openspeech.bytedance.com"


class DoubaoClient:
    """火山引擎 Doubao API 客户端。

    支持两种后端:
    - ARK Chat API (ark.cn-beijing.volces.com): Chat 对话、视觉 OCR
    - 豆包语音 API (openspeech.bytedance.com): TTS 语音合成
    """

    def __init__(
        self,
        api_key: str = "",
        app_id: str = "",
        access_token: str = "",
        base_url: str = ARK_BASE_URL,
        voice_base_url: str = VOICE_BASE_URL,
        vision_model: str = "doubao-seed-evolving",
        tts_model: str = "",
    ):
        self.api_key = api_key or settings.doubao_api_key
        self.app_id = app_id or settings.doubao_app_id
        self.access_token = access_token or settings.doubao_access_token
        self.base_url = base_url
        self.voice_base_url = voice_base_url
        self.vision_model = vision_model
        self.tts_model = tts_model or settings.doubao_tts_model
        self._stt_resource_id = settings.doubao_voice_resource_id_stt
        self._tts_resource_id = settings.doubao_voice_resource_id_tts

    # ── ARK Chat API (OCR) ──

    @property
    def _ark_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def _voice_headers(self) -> dict:
        """豆包语音 API 认证头（新版 + 旧版兼容）。"""
        return {
            "X-Api-App-Key": self.app_id,
            "X-Api-Access-Key": self.access_token,
            "Content-Type": "application/json",
        }

    async def ocr_image(self, image_bytes: bytes) -> str:
        """对图片/PDF进行OCR提取文本。

        使用 Doubao 视觉模型识别报告中的文字内容。
        """
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/png;base64,{b64}"

        payload = {
            "model": self.vision_model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {
                            "type": "text",
                            "text": (
                                "请仔细识别并提取这份医学报告中的所有文字内容，"
                                "包括检查项目、检测结果、参考范围、异常标记等。"
                                "不要总结或解释，只输出原文内容。"
                            ),
                        },
                    ],
                }
            ],
            "max_tokens": 4096,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._ark_headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    # ── TTS (语音合成) — 豆包语音 API ──

    async def text_to_speech(
        self, text: str, voice: str = "zh_female_qingxin", speed: float = 1.0
    ) -> bytes:
        """将文本合成为语音（MP3格式）。

        Args:
            text: 要合成的文本
            voice: 音色标识
            speed: 语速，范围[-50,100]，100=2.0倍速，-50=0.5倍速

        Returns:
            MP3 音频字节流
        """
        # 语速转换: speed 0.5-2.0 → speech_rate -50~100
        speech_rate = int((speed - 1.0) * 100)
        speech_rate = max(-50, min(100, speech_rate))

        payload = {
            "model": self.tts_model,
            "text_prompt": text,
            "audio_config": {
                "format": "mp3",
                "sample_rate": 24000,
                "speech_rate": speech_rate,
            },
            "watermark": {},
        }

        headers = self._voice_headers.copy()
        if self._tts_resource_id:
            headers["X-Api-Resource-Id"] = self._tts_resource_id

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.voice_base_url}/api/v3/tts/create",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            audio_b64 = data.get("audio", "")
            if audio_b64:
                return base64.b64decode(audio_b64)
            # 如果返回了URL，下载音频
            audio_url = data.get("url", "")
            if audio_url:
                dl_resp = await client.get(audio_url)
                dl_resp.raise_for_status()
                return dl_resp.content
            raise ValueError(f"TTS 响应中未找到音频数据: {data}")

    # ── STT (语音识别) — 豆包语音 WebSocket API ──

    async def speech_to_text(self, audio_bytes: bytes, audio_format: str = "wav") -> str:
        """将音频字节流转写为文本。

        使用豆包语音流式语音识别 WebSocket API。

        Args:
            audio_bytes: 音频数据 (WAV/PCM)
            audio_format: 音频格式 (wav/pcm)

        Returns:
            转写后的文本
        """
        try:
            from websockets.asyncio.client import connect
        except ImportError:
            raise ImportError(
                "需要 websockets 库: pip install websockets"
            )

        req_id = str(uuid.uuid4())
        ws_headers = {
            "X-Api-App-Key": self.app_id,
            "X-Api-Access-Key": self.access_token,
            "X-Api-Resource-Id": self._stt_resource_id,
            "X-Api-Request-Id": req_id,
            "X-Api-Sequence": "-1",
        }

        ws_url = f"wss://openspeech.bytedance.com/api/v3/sauc/bigmodel"
        result_text = ""
        seq = 2

        async with connect(
            ws_url,
            additional_headers=ws_headers,
            max_size=10_000_000,
            open_timeout=10,
        ) as ws:
            # 1. 发送 full client request
            format_type = "pcm" if audio_format == "pcm" else "wav"
            body = json.dumps({
                "user": {"uid": "1"},
                "audio": {
                    "format": format_type,
                    "rate": 16000,
                    "bits": 16,
                    "channel": 1,
                },
                "request": {"model_name": "bigmodel"},
            }).encode()
            await ws.send(
                bytes([0x11, 0x10, 0x10, 0x00])
                + len(body).to_bytes(4, "big")
                + body
            )

            # 2. 发送音频数据包 (每包 200ms ≈ 6400 bytes @16kHz 16bit mono)
            chunk_size = 6400
            for offset in range(0, len(audio_bytes), chunk_size):
                chunk = audio_bytes[offset : offset + chunk_size]
                frame = (
                    bytes([0x11, 0x21, 0x10, 0x00])
                    + seq.to_bytes(4, "big")
                    + len(chunk).to_bytes(4, "big")
                    + chunk
                )
                await ws.send(frame)
                seq += 1

            # 3. 发送结束包
            end = (
                bytes([0x11, 0x23, 0x10, 0x00])
                + (-seq).to_bytes(4, "big", signed=True)
                + (0).to_bytes(4, "big")
            )
            await ws.send(end)

            # 4. 接收结果
            while True:
                try:
                    resp = await asyncio.wait_for(ws.recv(), timeout=15)
                    if len(resp) <= 8:
                        continue
                    msg_type = resp[1] >> 4
                    if msg_type == 0x09:  # full server response
                        # 解析 payload (flags 指示是否有 sequence num)
                        flags = resp[1] & 0x0F
                        offset_in_resp = 8
                        if flags & 1:
                            offset_in_resp = 12  # skip 4B sequence
                        plen = int.from_bytes(resp[4:8], "big")
                        if flags & 1:
                            # 实际 payload 在 sequence 之后
                            payload_start = 12
                            plen = int.from_bytes(resp[8:12], "big") if len(resp) > 12 else plen
                        else:
                            payload_start = 8
                            plen = int.from_bytes(resp[4:8], "big")
                        
                        payload_data = resp[payload_start : payload_start + plen]
                        try:
                            data = json.loads(payload_data.decode("utf-8"))
                            text = (
                                data.get("result", {})
                                .get("text", "")
                                or data.get("payload", {})
                                .get("text", "")
                            )
                            if text:
                                result_text = text
                            if data.get("request", {}).get("definite", False):
                                break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass
                    elif msg_type == 0x0F:  # 错误
                        try:
                            err_text = resp[12:].decode(errors="replace")
                            logger.error(f"STT 识别错误: {err_text}")
                        except Exception:
                            pass
                        break
                except asyncio.TimeoutError:
                    break

        return result_text


_doubao_client: Optional[DoubaoClient] = None


def get_doubao_client() -> DoubaoClient:
    """获取 DoubaoClient 懒加载单例。"""
    global _doubao_client
    if _doubao_client is None:
        _doubao_client = DoubaoClient()
    return _doubao_client
