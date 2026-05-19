# 任务 R4：基于候选商品的 AI 解释生成

## 目标

让大模型只基于后端选出的候选商品生成解释文案，避免凭空推荐。

## 范围

需要实现：

- 后端先产出 Top N 商品。
- LLM prompt 中只给这些候选商品和推荐证据。
- LLM 输出推荐说明、取舍建议、是否需要追问。
- 前端仍展示后端返回的商品卡片。
- 候选商品为空时，LLM 不得编造商品，必须说明信息不足或建议用户补充条件。

不做：

- 不允许 LLM 输出商品库外商品作为卡片。
- 不在本任务里做 LLM rerank。

## Prompt 约束

要求 LLM：

- 只能解释候选商品。
- 不得新增商品名。
- 如果信息不足，提出一个关键追问。
- 推荐理由要和后端 evidence 对齐。

## 验收标准

- AI 文本中出现的商品都能在商品卡片中找到。
- 商品卡片顺序以后端排序为准。
- 没有商品时，AI 应该追问或解释暂无合适商品。
- 文案不输出内部打分细节。

## 风险点

- LLM 可能仍会自由发挥，需要输出后校验商品名或 product_id。
- 文案要自然，不能像后台日志。

## 本轮实施边界

当前 R3 已完成：

- `RecommendationResult.products` 是后端排序后的候选商品。
- `RecommendationResult.scores` 包含每个商品的规则推荐证据。
- `ProductCard.reason` 已来自规则 evidence。

因此本轮实现：

- 聊天推荐 prompt 注入候选商品、product_id、价格、推荐证据、惩罚提示。
- 组合礼单 prompt 注入同样的 evidence。
- 候选商品为空时，prompt 明确要求追问，不允许推荐商品库外商品。
- 不改变前端卡片来源，前端仍只展示后端 `ProductCard`。

## 本轮执行记录

已完成：

- 更新 `backend/app/agent/prompts_lib/chat_recommendation.py`：
  - 候选商品 prompt 增加 `evidence / penalties`
  - 明确 LLM 只能解释候选商品
  - 明确不得新增商品名称、product_id、品牌或型号
  - 候选商品为空时，要求说明信息不足或追问，不允许编造商品
- 更新 `backend/app/agent/prompts_lib/gift_plan.py`：
  - 组合礼单 prompt 增加 evidence 和 penalties
  - 结构化 JSON 输出指令增加候选商品白名单约束
  - 候选为空时要求追问或说明暂无合适商品
- 更新 `backend/app/agent/graph.py`：
  - 保留空候选列表传入 prompt，避免空候选时退化成无限制回答
- 更新 `backend/app/services/chat_service.py`：
  - 将 `RecommendationResult.scores` 转成候选商品 evidence 注入聊天 prompt
- 更新 `backend/app/services/gift_plan_service.py`：
  - 将 `RecommendationResult.scores` 转成候选商品 evidence 注入组合礼单 prompt

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

Prompt 约束验证：

```text
chat_has_evidence True
empty_has_no_candidate_instruction True
plan_has_evidence True
```

接口验证：

- `POST /api/gift-plan/generate` 返回 200
- `POST /api/chat/stream` 返回 200
- `gift-plan` 示例回答围绕后端候选商品解释，没有新增商品卡片来源

后续可继续做：

- 增加 answer 校验器，检测 LLM 文本中是否出现候选商品外的 product_id。
- 在 R6 LLM rerank 中复用同样的候选白名单约束。
- 在调试日志中记录候选商品 evidence，便于排查文案和卡片不一致。
