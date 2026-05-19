"""商品重排序 prompt 预留位。

任务 6 暂不强制启用，仅做占位以保持子包结构完整。
未来可在 `RecommendationService` 中调用 LLM 对候选商品做轻量重排。
"""

PRODUCT_RERANK_PROMPT = (
    "你将看到一批候选商品和用户需求，请按与需求的相关程度对商品 product_id 进行重排，"
    "仅输出 JSON 数组：例如 [\"PROD-A\", \"PROD-B\"]，不要输出任何额外文本。"
)