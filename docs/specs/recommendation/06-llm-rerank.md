# 任务 R6：LLM Rerank 候选商品精排

## 目标

让大模型在后端已召回并打分的候选商品中做精排，提升复杂语义场景的排序质量。

## 范围

需要实现：

- 输入候选商品列表、规则分数和 GiftIntent。
- LLM 返回 product_id 排序和简短理由。
- 后端校验 LLM 只返回候选集内 product_id。
- 失败时回退规则排序。

不做：

- 不让 LLM 直接访问全量商品库。
- 不允许 LLM 新增商品。

## 建议输出

```json
{
  "ranked_product_ids": ["PROD-1", "PROD-2"],
  "reasons": {
    "PROD-1": "更符合见家长场景的体面感"
  }
}
```

## 验收标准

- LLM rerank 结果稳定在候选集内。
- 非法 product_id 被忽略。
- LLM 超时或解析失败时，系统使用规则排序。
- 日志能区分规则排序和 LLM rerank 排序。

## 风险点

- Rerank prompt 不宜过长，候选数量建议 10-20 个。
- 大模型可能偏好文案更漂亮的商品，需要结合规则分数约束。

