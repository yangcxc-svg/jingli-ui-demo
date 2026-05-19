# 任务 4：后端推荐服务抽象

## 目标

把聊天推荐、组合礼单推荐、商品卡片构建统一到一个后端推荐服务里，避免逻辑重复和行为不一致。

## 当前问题

- `chat_service.py` 和 `gift_plan_service.py` 都在做商品检索和商品卡片构建。
- 推荐文本和商品卡片之间没有稳定结构化关系。
- 后续如果升级推荐策略，需要改多个服务。
- 完成任务 3 后，礼单已持久化；因此商品推荐输出更需要稳定的 `ProductCard` 快照字段。

## 范围

需要实现：

- 新增 `RecommendationService`。
- 统一输入：用户意图、场景、预算、偏好、历史对话。
- 统一输出：推荐文本、商品卡片、推荐理由、引用信息。
- 聊天接口和组合礼单接口复用该服务。
- 本轮先统一“检索 + 商品卡片构建 + 预算过滤 + 兜底商品”，不改动现有流式文本生成方式。

不做：

- 不立即替换所有 RAG 实现。
- 不强制引入复杂 Agent 框架。

## 建议数据结构

```py
class RecommendationRequest(BaseModel):
    message: str
    scenario: str | None = None
    budget: Decimal | None = None
    preference: str | None = None
    conversation_id: str | None = None

class RecommendationResult(BaseModel):
    answer: str
    products: list[ProductCard]
    citations: list[Citation]
    intent: str | None = None
```

## 影响文件

- `backend/app/services/chat_service.py`
- `backend/app/services/gift_plan_service.py`
- `backend/app/services/recommendation_service.py`
- `backend/app/schemas/recommendation.py`

## 本轮实施边界

本轮目标是低风险抽象，不改变外部接口：

- 新增 `backend/app/schemas/recommendation.py`。
- 新增 `backend/app/services/recommendation_service.py`。
- `ChatService.stream_chat` 使用 `RecommendationService.recommend_products` 获取商品卡片和 citations 数量。
- `GiftPlanService.generate` 使用 `RecommendationService.recommend_products` 获取组合商品和兜底商品。
- 暂不把 `GuideAgent.astream` 移进 `RecommendationService`，避免破坏 SSE 时序。

## 验收标准

- `/api/chat/stream` 行为不退化。
- `/api/gift-plan/generate` 行为不退化。
- 商品卡片构建逻辑只保留一份。
- 单测覆盖推荐服务的预算过滤、去重、兜底商品逻辑。

## 风险点

- 流式聊天需要边生成边返回，而组合礼单可以一次性返回，服务抽象要兼容这两种模式。
- 不要把前端展示字段泄漏到模型 prompt 里。

## 本轮执行记录

已完成：

- 新增 `backend/app/schemas/recommendation.py`。
- 新增 `backend/app/services/recommendation_service.py`。
- `RecommendationService` 统一负责：
  - 知识检索 query 组装
  - `ProductCard` 构建
  - 商品去重
  - 预算过滤
  - 兜底商品选择
- `ChatService.stream_chat` 已改为通过 `RecommendationService.recommend_products` 获取商品卡片和 citations 数量。
- `GiftPlanService.generate` 已改为通过 `RecommendationService.recommend_products` 获取组合商品。
- 删除了 `chat_service.py` 和 `gift_plan_service.py` 中重复的商品卡片构建逻辑。

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

手动验证推荐服务兜底商品：

```text
fallback_count 2
first_product PROD-EARBUDS-001
```

使用 FastAPI `TestClient` 手动验证：

- `POST /api/gift-plan/generate` 返回 200，返回 4 个商品，组合总价正常。
- `POST /api/chat/stream` 返回 200，SSE 文本正常返回。

后续可继续做：

- 将 Agent 文本生成也纳入 `RecommendationService` 的统一结果模型。
- 为预算过滤、去重、兜底商品补自动化单测。
- 让模型输出 `selected_product_ids`，进一步稳定文本和商品卡片的对应关系。
