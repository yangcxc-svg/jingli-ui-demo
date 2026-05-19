"""LLM client with provider routing & optional vision support.

Supported providers (selected via settings.llm_provider):

- "mock"               -> 离线占位，原行为
- "openai"             -> 官方 OpenAI
- "deepseek"           -> https://api.deepseek.com/v1
- "dashscope"          -> 阿里通义 https://dashscope.aliyuncs.com/compatible-mode/v1
- "zhipu"              -> 智谱 https://open.bigmodel.cn/api/paas/v4
- "moonshot"           -> Kimi https://api.moonshot.cn/v1
- "ollama"             -> 本地 http://host.docker.internal:11434/v1
- "openai_compatible"  -> 任意 OpenAI 兼容端点（用 llm_base_url 指定）

所有 provider 均通过 OpenAI Chat Completions 协议调用；Ollama 11434/v1 也兼容此协议。
带图片调用时使用多模态 content 数组（{"type":"text"} + {"type":"image_url"}）。
"""

from __future__ import annotations

import base64
import json
import logging
import time
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.services.model_log_service import model_log_service

logger = logging.getLogger(__name__)


class LLMResult(BaseModel):
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


class ImageRef(BaseModel):
    """Image reference passed to LLM. Either a local file path or a remote URL."""

    path: str | None = None
    url: str | None = None
    content_type: str = "image/jpeg"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


_PROVIDER_DEFAULT_BASE_URL: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "moonshot": "https://api.moonshot.cn/v1",
    "ollama": "http://host.docker.internal:11434/v1",
}


def _resolve_base_url(provider: str) -> str:
    if settings.llm_base_url:
        return settings.llm_base_url.rstrip("/")
    return _PROVIDER_DEFAULT_BASE_URL.get(provider, "").rstrip("/")


def _file_to_data_url(path: str, content_type: str) -> str:
    raw = Path(path).read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{content_type};base64,{b64}"


def _build_user_content(
    prompt: str, images: list[ImageRef] | None
) -> str | list[dict[str, Any]]:
    """无图片时返回纯字符串（兼容旧 provider），有图片时返回多模态数组。"""
    if not images:
        return prompt
    parts: list[dict[str, Any]] = []
    for img in images:
        url = img.url
        if not url and img.path:
            try:
                url = _file_to_data_url(img.path, img.content_type)
            except Exception:  # noqa: BLE001
                logger.exception("image_encode_failed path=%s", img.path)
                continue
        if url:
            parts.append({"type": "image_url", "image_url": {"url": url}})
    parts.append({"type": "text", "text": prompt})
    return parts


def _build_messages(
    prompt: str,
    system: str | None,
    images: list[ImageRef] | None = None,
    history: list[ChatMessage] | None = None,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if system:
        messages.append({"role": "system", "content": system})
    for item in history or []:
        if item.content.strip():
            messages.append({"role": item.role, "content": item.content})
    messages.append({"role": "user", "content": _build_user_content(prompt, images)})
    return messages


def _auth_headers(provider: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if provider == "ollama":
        return headers
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"
    return headers


class LLMClient:
    """Thin OpenAI-compatible Chat Completions client (with vision support)."""

    def __init__(self) -> None:
        self.provider = (settings.llm_provider or "mock").lower()
        self.model = settings.llm_model or "mock-guide"
        self.base_url = _resolve_base_url(self.provider)
        # Vision models 通常处理更慢，timeout 放宽
        self.timeout = httpx.Timeout(120.0, connect=10.0)

    @property
    def is_mock(self) -> bool:
        return self.provider == "mock"

    def status(self) -> dict[str, Any]:
        """返回当前 LLM 配置摘要（用于 /health/ready），不暴露 API Key。"""
        return {
            "provider": self.provider,
            "model": self.model,
            "is_mock": self.is_mock,
            "base_url_configured": bool(self.base_url),
            "api_key_configured": bool(settings.llm_api_key),
        }

    # ---------- public API ----------

    async def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        images: list[ImageRef] | None = None,
        history: list[ChatMessage] | None = None,
        prompt_name: str = "generate",
        prompt_version: str = "v1",
        trace_id: str | None = None,
    ) -> LLMResult:
        if self.provider == "mock":
            tag = f" (+{len(images)} images)" if images else ""
            model_log_service.record(
                provider=self.provider,
                model=self.model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                latency_ms=0,
                status="success",
                is_mock=True,
                is_stream=False,
                trace_id=trace_id,
            )
            return LLMResult(text=f"Mock LLM response.{tag}")

        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": _build_messages(prompt, system, images, history),
            "temperature": temperature,
            "stream": False,
        }
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.post(url, headers=_auth_headers(self.provider), json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.exception("llm_generate_failed provider=%s err=%s", self.provider, exc)
            model_log_service.record(
                provider=self.provider,
                model=self.model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="error",
                error=str(exc),
                is_mock=False,
                is_stream=False,
                trace_id=trace_id,
            )
            return LLMResult(text=f"[LLM 调用失败] {exc}")

        text = self._extract_text(data)
        usage = data.get("usage") or {}
        latency_ms = int((time.perf_counter() - started) * 1000)
        input_tokens = int(usage.get("prompt_tokens") or 0)
        output_tokens = int(usage.get("completion_tokens") or 0)
        model_log_service.record(
            provider=self.provider,
            model=self.model,
            prompt_name=prompt_name,
            prompt_version=prompt_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            status="success",
            is_mock=False,
            is_stream=False,
            trace_id=trace_id,
        )
        return LLMResult(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )

    async def astream(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        images: list[ImageRef] | None = None,
        history: list[ChatMessage] | None = None,
        prompt_name: str = "stream",
        prompt_version: str = "v1",
        trace_id: str | None = None,
    ) -> AsyncIterator[str]:
        """异步流式 yield 每个 token/delta 文本。"""
        if self.provider == "mock":
            tag = f" (+{len(images)} images)" if images else ""
            for token in f"Mock LLM response.{tag}".split(" "):
                yield token + " "
            model_log_service.record(
                provider=self.provider,
                model=self.model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                latency_ms=0,
                status="success",
                is_mock=True,
                is_stream=True,
                trace_id=trace_id,
            )
            return

        url = f"{self.base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": _build_messages(prompt, system, images, history),
            "temperature": temperature,
            "stream": True,
        }
        started = time.perf_counter()
        success = True
        error_message: str | None = None
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST", url, headers=_auth_headers(self.provider), json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[len("data:") :].strip()
                        if not data_str or data_str == "[DONE]":
                            if data_str == "[DONE]":
                                break
                            continue
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue
                        delta = (
                            chunk.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content")
                        )
                        if delta:
                            yield delta
        except httpx.HTTPError as exc:
            logger.exception("llm_stream_failed provider=%s err=%s", self.provider, exc)
            success = False
            error_message = str(exc)
            yield f"\n[LLM 流式调用失败] {exc}"
        finally:
            model_log_service.record(
                provider=self.provider,
                model=self.model,
                prompt_name=prompt_name,
                prompt_version=prompt_version,
                latency_ms=int((time.perf_counter() - started) * 1000),
                status="success" if success else "error",
                error=error_message,
                is_mock=False,
                is_stream=True,
                trace_id=trace_id,
            )

    # ---------- internal ----------

    @staticmethod
    def _extract_text(data: dict[str, Any]) -> str:
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError):
            return json.dumps(data, ensure_ascii=False)
