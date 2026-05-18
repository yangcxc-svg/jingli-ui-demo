"""Evaluation service.

- summary：返回 MetricsCollector 实时聚合（无需后台任务，秒级响应）
- run：对内置 3 条 golden 问题做一次 self-test，把结果一并写入 collector，
  让前端"命中率/幻觉率"两个指标立即有数据。
"""

from __future__ import annotations

from uuid import uuid4

from app.metrics.collector import MetricsCollector
from app.schemas.chat import ChatRequest
from app.schemas.eval import EvalRunResponse, EvalSummaryResponse
from app.services.chat_service import ChatService

GOLDEN_QUESTIONS: list[str] = [
    "Nimbus Air Pro NA-P12 的降噪深度是多少？",
    "预算 1500 元，地铁通勤场景，推荐哪一款？",
    "NA-P10 / NA-P11 / NA-P12 的主要差异是什么？",
]


class EvalService:
    def __init__(self) -> None:
        self.metrics = MetricsCollector()

    async def run(self) -> EvalRunResponse:
        chat_service = ChatService()
        executed = 0
        failures = 0
        for q in GOLDEN_QUESTIONS:
            try:
                req = ChatRequest(conversation_id=None, message=q, image_ids=[])
                await chat_service.chat(req)
                executed += 1
            except Exception:  # noqa: BLE001
                failures += 1
        return EvalRunResponse(
            eval_run_id=str(uuid4()),
            status="done" if failures == 0 else "partial",
            executed=executed,
            failures=failures,
        )

    async def summary(self) -> EvalSummaryResponse:
        snap = self.metrics.snapshot()
        status = "ready" if int(snap.get("total_chats", 0) or 0) > 0 else "empty"
        return EvalSummaryResponse(
            status=status,
            metrics=snap,
            recent=self.metrics.recent_chats(n=8),
        )