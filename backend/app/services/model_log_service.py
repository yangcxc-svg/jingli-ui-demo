"""模型调用日志（内存版单例）。

任务 6 用于记录每次 LLM 请求的 provider / model / latency / tokens / 错误信息，
不写库，不阻塞主流程。后续若接入数据库版，可保留同样的 record 接口。
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class ModelCallRecord:
    trace_id: str
    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    status: Literal["success", "error"]
    error: str | None = None
    is_mock: bool = False
    is_stream: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


class ModelLogService:
    """单例：保存最近 N 条模型调用日志，写入失败仅 warn 不抛错。"""

    _instance: "ModelLogService | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "ModelLogService":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._records = deque(maxlen=200)  # type: ignore[attr-defined]
                cls._instance = inst
        return cls._instance

    _records: deque[ModelCallRecord]

    def record(
        self,
        *,
        provider: str,
        model: str,
        prompt_name: str,
        prompt_version: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: int = 0,
        status: Literal["success", "error"] = "success",
        error: str | None = None,
        is_mock: bool = False,
        is_stream: bool = False,
        trace_id: str | None = None,
    ) -> None:
        try:
            self._records.append(
                ModelCallRecord(
                    trace_id=trace_id or str(uuid4()),
                    provider=provider,
                    model=model,
                    prompt_name=prompt_name,
                    prompt_version=prompt_version,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    status=status,
                    error=error,
                    is_mock=is_mock,
                    is_stream=is_stream,
                )
            )
        except Exception:  # noqa: BLE001
            logger.warning("model_log_record_failed", exc_info=True)

    def recent(self, limit: int = 20) -> list[dict[str, object]]:
        items = list(self._records)[-limit:][::-1]
        result: list[dict[str, object]] = []
        for item in items:
            data = asdict(item)
            data["created_at"] = item.created_at.isoformat() + "Z"
            result.append(data)
        return result

    def reset(self) -> None:
        self._records.clear()


model_log_service = ModelLogService()