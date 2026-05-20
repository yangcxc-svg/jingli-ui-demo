"""In-process metrics collector for the MVP.

不依赖任何外部存储；仅在当前 backend 进程内汇总最近 N 条对话与反馈，用于侧栏
"质量评测" 面板的实时展示。重启后清空（评测数据本就是观测性指标，可重建）。

指标定义（按 DEV_SPEC v1.3）：

- **命中率 (citation_rate)**：assistant 回答中携带 >=1 条 citation 的占比。
  作为 RAG 检索是否被利用的近似上界。
- **推荐准确率 (satisfaction_rate)**：好评 / (好评 + 差评)。当反馈样本数 < 3 时返回 null。
- **幻觉率 (hallucination_rate)**：无 citation 且回答字数 >= 30 的占比。
  无知识库支撑却给出确定性长答案的近似下界。
- 附加：total_chats、total_feedback、avg_latency_ms、avg_answer_chars
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


@dataclass
class ChatRecord:
    query: str
    answer_chars: int
    citation_count: int
    latency_ms: int
    has_images: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FeedbackRecord:
    message_id: str
    rating: Literal["up", "down"]
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RecommendationEvalRecord:
    eval_run_id: str
    case_id: str
    query: str
    strategy: str
    returned_count: int
    candidate_count: int
    needs_clarification: bool
    scenario_hit: bool
    target_hit: bool
    budget_hit: bool
    avoid_violation: bool
    duplicate_count: int
    top_product_ids: list[str]
    created_at: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """Singleton metrics collector. Keeps last `max_records` entries in memory."""

    _instance: "MetricsCollector | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "MetricsCollector":
        with cls._lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._chats = deque(maxlen=500)  # type: ignore[attr-defined]
                inst._feedbacks = deque(maxlen=500)  # type: ignore[attr-defined]
                inst._recommendation_evals = deque(maxlen=500)  # type: ignore[attr-defined]
                cls._instance = inst
        return cls._instance

    # mypy hints
    _chats: deque[ChatRecord]
    _feedbacks: deque[FeedbackRecord]
    _recommendation_evals: deque[RecommendationEvalRecord]

    # ---------- write ----------

    def record_chat(
        self,
        *,
        query: str,
        answer_chars: int,
        citation_count: int,
        latency_ms: int,
        has_images: bool = False,
    ) -> None:
        self._chats.append(
            ChatRecord(
                query=query[:200],
                answer_chars=answer_chars,
                citation_count=citation_count,
                latency_ms=latency_ms,
                has_images=has_images,
            )
        )

    def record_feedback(self, message_id: str, rating: Literal["up", "down"]) -> None:
        self._feedbacks.append(FeedbackRecord(message_id=message_id, rating=rating))

    def record_recommendation_eval(
        self,
        *,
        eval_run_id: str,
        case_id: str,
        query: str,
        strategy: str,
        returned_count: int,
        candidate_count: int,
        needs_clarification: bool,
        scenario_hit: bool,
        target_hit: bool,
        budget_hit: bool,
        avoid_violation: bool,
        duplicate_count: int,
        top_product_ids: list[str],
    ) -> None:
        self._recommendation_evals.append(
            RecommendationEvalRecord(
                eval_run_id=eval_run_id,
                case_id=case_id,
                query=query[:200],
                strategy=strategy,
                returned_count=returned_count,
                candidate_count=candidate_count,
                needs_clarification=needs_clarification,
                scenario_hit=scenario_hit,
                target_hit=target_hit,
                budget_hit=budget_hit,
                avoid_violation=avoid_violation,
                duplicate_count=duplicate_count,
                top_product_ids=top_product_ids[:10],
            )
        )

    def reset(self) -> None:
        self._chats.clear()
        self._feedbacks.clear()
        self._recommendation_evals.clear()

    # ---------- read ----------

    def snapshot(self) -> dict[str, object]:
        chats = list(self._chats)
        feedbacks = list(self._feedbacks)
        rec_evals = list(self._recommendation_evals)

        total_chats = len(chats)
        total_fb = len(feedbacks)

        # 命中率
        with_citation = sum(1 for c in chats if c.citation_count > 0)
        citation_rate = (with_citation / total_chats) if total_chats else 0.0

        # 推荐准确率
        ups = sum(1 for f in feedbacks if f.rating == "up")
        downs = sum(1 for f in feedbacks if f.rating == "down")
        if (ups + downs) >= 3:
            satisfaction_rate: float | None = ups / (ups + downs)
        else:
            satisfaction_rate = None

        # 幻觉率
        long_no_cite = sum(
            1 for c in chats if c.citation_count == 0 and c.answer_chars >= 30
        )
        hallucination_rate = (long_no_cite / total_chats) if total_chats else 0.0

        # 平均延迟 / 字数（仅对最近 50 条）
        recent = chats[-50:]
        avg_latency = (
            int(sum(c.latency_ms for c in recent) / len(recent)) if recent else 0
        )
        avg_answer_chars = (
            int(sum(c.answer_chars for c in recent) / len(recent)) if recent else 0
        )

        # 状态判定：用于前端显示颜色
        def _status_citation(r: float) -> str:
            if total_chats < 3:
                return "warming"
            if r >= 0.7:
                return "good"
            if r >= 0.4:
                return "warn"
            return "bad"

        def _status_sat(r: float | None) -> str:
            if r is None:
                return "warming"
            if r >= 0.7:
                return "good"
            if r >= 0.4:
                return "warn"
            return "bad"

        def _status_halluc(r: float) -> str:
            if total_chats < 3:
                return "warming"
            if r <= 0.1:
                return "good"
            if r <= 0.3:
                return "warn"
            return "bad"

        return {
            "total_chats": total_chats,
            "total_feedback": total_fb,
            "feedback_up": ups,
            "feedback_down": downs,
            "avg_latency_ms": avg_latency,
            "avg_answer_chars": avg_answer_chars,
            "citation_rate": round(citation_rate, 4),
            "citation_status": _status_citation(citation_rate),
            "satisfaction_rate": (
                round(satisfaction_rate, 4) if satisfaction_rate is not None else None
            ),
            "satisfaction_status": _status_sat(satisfaction_rate),
            "hallucination_rate": round(hallucination_rate, 4),
            "hallucination_status": _status_halluc(hallucination_rate),
            "recommendation_eval_total": len(rec_evals),
            "recommendation_eval_summary": self._summarize_recommendation_evals(rec_evals),
        }

    def recent_chats(self, n: int = 10) -> list[dict[str, object]]:
        return [
            {
                "query": c.query,
                "answer_chars": c.answer_chars,
                "citation_count": c.citation_count,
                "latency_ms": c.latency_ms,
                "has_images": c.has_images,
                "created_at": c.created_at.isoformat() + "Z",
            }
            for c in list(self._chats)[-n:][::-1]
        ]

    def recent_recommendation_evals(self, n: int = 10) -> list[dict[str, object]]:
        return [
            {
                "eval_run_id": item.eval_run_id,
                "case_id": item.case_id,
                "query": item.query,
                "strategy": item.strategy,
                "returned_count": item.returned_count,
                "candidate_count": item.candidate_count,
                "needs_clarification": item.needs_clarification,
                "scenario_hit": item.scenario_hit,
                "target_hit": item.target_hit,
                "budget_hit": item.budget_hit,
                "avoid_violation": item.avoid_violation,
                "duplicate_count": item.duplicate_count,
                "top_product_ids": item.top_product_ids,
                "created_at": item.created_at.isoformat() + "Z",
            }
            for item in list(self._recommendation_evals)[-n:][::-1]
        ]

    @staticmethod
    def _summarize_recommendation_evals(
        records: list[RecommendationEvalRecord],
    ) -> dict[str, object]:
        if not records:
            return {
                "case_count": 0,
                "scenario_hit_rate": 0.0,
                "target_hit_rate": 0.0,
                "budget_hit_rate": 0.0,
                "avoid_violation_rate": 0.0,
                "clarification_rate": 0.0,
                "avg_returned_count": 0.0,
                "duplicate_rate": 0.0,
            }

        total = len(records)
        return {
            "case_count": total,
            "scenario_hit_rate": round(sum(1 for item in records if item.scenario_hit) / total, 4),
            "target_hit_rate": round(sum(1 for item in records if item.target_hit) / total, 4),
            "budget_hit_rate": round(sum(1 for item in records if item.budget_hit) / total, 4),
            "avoid_violation_rate": round(
                sum(1 for item in records if item.avoid_violation) / total,
                4,
            ),
            "clarification_rate": round(
                sum(1 for item in records if item.needs_clarification) / total,
                4,
            ),
            "avg_returned_count": round(
                sum(item.returned_count for item in records) / total,
                2,
            ),
            "duplicate_rate": round(
                sum(1 for item in records if item.duplicate_count > 0) / total,
                4,
            ),
        }
