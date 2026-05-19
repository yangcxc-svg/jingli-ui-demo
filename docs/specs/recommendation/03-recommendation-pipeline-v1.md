# 任务 R3：推荐管线 V1：召回、打分、排序、返回

## 目标

把意图抽取、候选召回、规则打分和商品排序串成完整推荐管线。

## 范围

需要实现：

- `RecommendationService` 接收 `GiftIntent`。
- 先用结构化字段召回候选商品。
- 使用 `ProductScorer` 打分。
- 排序后返回 Top N 商品和分项推荐依据。
- 返回基础管线 trace，方便确认召回来源和候选数量。

不做：

- 不引入向量库。
- 不做 LLM rerank。

## 推荐流程

```text
用户文本
  -> GiftIntent
  -> 字段召回 candidates
  -> ProductScorer
  -> Top N ProductCard + score evidence
```

## 影响文件

```text
backend/app/services/recommendation_service.py
backend/app/services/intent_extractor.py
backend/app/services/product_scorer.py
backend/app/schemas/recommendation.py
```

## 验收标准

- 推荐商品来自商品库。
- 推荐排序可复现，同一输入在同一商品库下结果稳定。
- 商品卡片携带推荐理由，不依赖 LLM 编造。
- `/api/chat/stream` 和 `/api/gift-plan/generate` 都复用新管线。

## 风险点

- 召回过窄会导致无商品，需要有 fallback。
- 召回过宽会让排序质量下降，需要控制候选数量。

## 本轮实施边界

当前 R1/R2 已完成：

- R1：`GiftIntent` 可从用户输入解析出来。
- R2：`ProductScorer` 可对商品打分并返回证据。

因此本轮实现：

- `RecommendationService.recommend_products` 内部显式拆成：
  1. 意图解析
  2. 结构化字段召回
  3. 知识检索召回
  4. 兜底召回
  5. 合并去重
  6. 规则打分
  7. 排序截断 Top N
- `RecommendationResult` 增加 `pipeline`，记录召回数量、候选数量、返回数量。
- 商品卡片 `reason` 使用 `ProductScore.reasons[0]`，确保卡片推荐理由来自后端规则证据。

## 本轮执行记录

已完成：

- 更新 `backend/app/schemas/recommendation.py`：
  - `RecommendationRequest` 增加 `max_candidates`
  - `RecommendationResult` 增加 `pipeline`
- 更新 `backend/app/services/recommendation_service.py`：
  - `recommend_products` 显式拆成推荐管线
  - 新增 `structured_recall_candidates`
  - 新增 `_merge_candidates`
  - 保留知识检索召回，并与结构化召回合并去重
  - 支持放宽召回，避免结构化字段过窄导致无商品
  - 保留兜底召回
  - 使用 `ProductScorer` 统一打分排序
  - 返回 Top N 商品、对应 `scores` 和 `pipeline` trace
  - 商品卡片 `reason` 改为来自 `ProductScore.reasons[0]`
- 修正预算档位逻辑：
  - 用户给出明确预算时，不再强制使用 `budget_level` 过滤
  - 由价格过滤负责约束预算，避免 500 元预算误伤 low 档商品

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

推荐管线稳定性验证：

```text
输入：想给25岁女生送生日礼物，预算500元。
pipeline = {
  structured_recall_count: 0,
  knowledge_recall_count: 0,
  relaxed_recall_count: 2,
  fallback_recall_count: 0,
  candidate_count: 2,
  returned_count: 2
}
products = ['PROD-EARBUDS-001', 'PROD-BAND-001']
scores = [26.9, 18.1]
stable = True
```

接口验证：

- `POST /api/gift-plan/generate` 返回 200
- `POST /api/chat/stream` 返回 200

后续可继续做：

- R4：让 LLM 解释只基于推荐管线输出的候选商品和 evidence。
- 给推荐管线增加自动化测试，覆盖候选合并去重、放宽召回、Top N 截断。
- 商品数据需要继续补齐更贴近送礼的 `scenarios / target_people`，让结构化召回命中率提高。
