from typing import Any

from pydantic import BaseModel


class EvalRunResponse(BaseModel):
    eval_run_id: str
    status: str
    executed: int = 0
    failures: int = 0


class EvalSummaryResponse(BaseModel):
    """实时质量评测指标快照。

    - citation_rate：命中率（带引用回答占比）
    - satisfaction_rate：推荐准确率（好评 /（好评+差评）），样本不足时为 None
    - hallucination_rate：幻觉率（无引用且回答较长的占比）
    - 各 *_status：good / warn / bad / warming（数据预热中）
    """

    status: str
    metrics: dict[str, Any]
    recent: list[dict[str, Any]] = []


class ModelLogListResponse(BaseModel):
    """模型调用日志列表（任务 6）。"""

    items: list[dict[str, Any]] = []