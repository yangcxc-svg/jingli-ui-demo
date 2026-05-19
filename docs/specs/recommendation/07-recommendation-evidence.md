# 任务 R7：推荐理由与打分证据结构化

## 目标

让推荐结果可解释、可调试、可展示。

## 范围

需要实现：

- 推荐结果包含 `score`、`matched_features`、`penalties`。
- 前端商品卡片可以展示简短推荐理由。
- 后端日志记录完整证据。

不做：

- 不把所有内部权重暴露给用户。

## 建议数据结构

```py
class RecommendationEvidence(BaseModel):
    product_id: str
    score: float
    matched_features: list[str]
    penalties: list[str]
    display_reason: str
```

## 验收标准

- 每个推荐商品都有 `display_reason`。
- Debug 日志可以看到分项分数。
- 用户看到的是自然理由，不是机械分数。

## 风险点

- 理由不能和真实规则矛盾。
- 前端展示要克制，避免信息过载。

