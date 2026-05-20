# 2026-05-20 推荐算法 R11-R15 迭代合并说明

## 基线节点

本轮迭代基于当前分支已有提交继续开发。

当前本地最新提交：

```text
3df9bee recommendation_task_update_r9
```

可把该提交视为本轮 R11-R15 算法迭代前的基线节点。若后续需要和他人分支 merge，可重点比较该提交之后的改动。

## 本轮迭代目标

本轮主要把京礼推荐从“聊天推荐商品”继续升级为“可控推荐算法 + 方案优化 + 完整送礼解决方案”。

核心变化：

- 候选不足时主动给出约束放宽建议。
- 引入预算约束下的组合优化方案。
- 让预算约束根据用户表达自动区分硬预算、软预算、可协商预算。
- 显式建模主礼 / 副礼。
- 前端展示主礼 / 副礼角标。
- 新增完整送礼方案能力：判断单品还是组合，并生成送礼话术、时机、地点、包装和避坑建议。

## 任务范围

### R11 约束放宽与候选不足协商

新增能力：

- 用户说“不喜欢这些，换一个”等负反馈时，系统能继承会话记忆。
- 过滤已推荐或不喜欢商品。
- 当候选不足、分数偏低、过滤过多时，返回 `relaxation_options`。
- 前端展示“可以这样调整”的建议 chips。

主要新增/修改：

```text
backend/app/services/constraint_relaxation_service.py
backend/app/schemas/recommendation.py
backend/app/schemas/chat.py
backend/app/services/recommendation_service.py
backend/app/services/chat_service.py
backend/app/agent/graph.py
backend/app/agent/prompts_lib/chat_recommendation.py
backend/app/services/eval_service.py
frontend/src/api/chat.ts
frontend/src/hooks/useGiftChat.ts
frontend/src/pages/AppPages.tsx
docs/specs/recommendation/11-constraint-relaxation-policy.md
```

### R12 预算约束组合优化与方案裁判

新增能力：

- 推荐服务会同时生成：
  - `ranked_topn`
  - `budget_optimized`
- 新增方案裁判，选择最终推荐方案。
- 方案返回预算利用率、目标函数、裁判理由等观测字段。

主要新增/修改：

```text
backend/app/services/budget_optimizer_service.py
backend/app/services/plan_judge_service.py
backend/app/schemas/recommendation.py
backend/app/services/recommendation_service.py
backend/app/services/eval_service.py
docs/specs/recommendation/12-budget-optimized-plan-judge.md
```

### R13 预算语义化与主副礼组合建模

新增能力：

- 用户预算表达被解析为：
  - `hard`
  - `soft`
  - `negotiable`
  - `unknown`
- 后端根据预算类型确定性计算：
  - `budget_flexibility`
  - `budget_upper_bound`
- 组合方案显式返回 `gift_roles`。

主要新增/修改：

```text
backend/app/schemas/gift_intent.py
backend/app/services/intent_extractor.py
backend/app/agent/prompts_lib/intent_extraction.py
backend/app/services/budget_optimizer_service.py
backend/app/services/plan_judge_service.py
backend/app/services/recommendation_service.py
backend/app/services/eval_service.py
docs/specs/recommendation/13-budget-semantics-main-addon-plan.md
```

### R14 主副礼方案解释与前端展示

新增能力：

- `ProductCard` 新增 `gift_role`。
- 流式 `product_cards` 事件携带主礼 / 副礼。
- Prompt 注入选中方案上下文，让大模型解释主礼、副礼和搭配逻辑。
- 前端商品卡片展示“主礼 / 副礼”角标。
- `/compare` 页面保留主副礼字段，便于 A/B 对比。

主要新增/修改：

```text
backend/app/schemas/product.py
backend/app/services/budget_optimizer_service.py
backend/app/services/recommendation_service.py
backend/app/services/chat_service.py
backend/app/agent/graph.py
backend/app/agent/prompts_lib/chat_recommendation.py
frontend/src/api/chat.ts
frontend/src/pages/AppPages.tsx
docs/specs/recommendation/14-plan-explanation-ui.md
```

### R15 礼物形态决策与完整送礼方案

新增能力：

- 新增礼物形态判断：
  - `single_gift`
  - `gift_combo`
  - `either`
- 新增完整送礼方案接口：
  - `POST /api/gift-solution/generate`
- 完整方案包含：
  - 推荐总结
  - 推荐理由
  - 商品卡片
  - 送礼话术
  - 送礼时机
  - 送礼地点
  - 包装建议
  - 对方推辞回应
  - 避坑提醒
- 前端新增 `/gift-solution` 页面。

主要新增/修改：

```text
backend/app/schemas/gift_solution.py
backend/app/services/gift_shape_service.py
backend/app/services/gift_solution_service.py
backend/app/agent/prompts_lib/gift_solution.py
backend/app/api/routes/gift_solution.py
backend/app/api/router.py
frontend/src/api/giftSolution.ts
frontend/src/App.tsx
frontend/src/pages/AppPages.tsx
docs/specs/recommendation/15-gift-shape-decision-solution.md
```

## 当前工作区涉及文件

### 后端新增文件

```text
backend/app/agent/prompts_lib/gift_solution.py
backend/app/api/routes/gift_solution.py
backend/app/schemas/gift_solution.py
backend/app/services/budget_optimizer_service.py
backend/app/services/constraint_relaxation_service.py
backend/app/services/gift_shape_service.py
backend/app/services/gift_solution_service.py
backend/app/services/plan_judge_service.py
```

### 后端修改文件

```text
backend/app/agent/graph.py
backend/app/agent/prompts_lib/chat_recommendation.py
backend/app/agent/prompts_lib/intent_extraction.py
backend/app/api/router.py
backend/app/api/routes/eval.py
backend/app/metrics/collector.py
backend/app/schemas/chat.py
backend/app/schemas/eval.py
backend/app/schemas/gift_intent.py
backend/app/schemas/product.py
backend/app/schemas/recommendation.py
backend/app/services/chat_service.py
backend/app/services/eval_service.py
backend/app/services/intent_extractor.py
backend/app/services/recommendation_service.py
```

### 前端新增文件

```text
frontend/src/api/giftSolution.ts
```

### 前端修改文件

```text
frontend/package-lock.json
frontend/src/App.tsx
frontend/src/api/chat.ts
frontend/src/hooks/useGiftChat.ts
frontend/src/pages/AppPages.tsx
```

### 文档新增/修改

```text
docs/specs/recommendation/10-evaluation-observability.md
docs/specs/recommendation/README.md
docs/specs/recommendation/11-constraint-relaxation-policy.md
docs/specs/recommendation/12-budget-optimized-plan-judge.md
docs/specs/recommendation/13-budget-semantics-main-addon-plan.md
docs/specs/recommendation/14-plan-explanation-ui.md
docs/specs/recommendation/15-gift-shape-decision-solution.md
docs/merge-notes/2026-05-20-recommendation-r11-r15.md
```

## 合并时重点关注

### 1. `frontend/src/pages/AppPages.tsx`

这是前端最容易冲突的文件。

本轮新增/修改内容包括：

- 主聊天商品卡片主礼 / 副礼角标。
- `/compare` 对比页面保留主副礼信息。
- 新增 `/gift-solution` 页面。
- 京礼首页新增“完整送礼方案”入口。

如果别人也改了页面结构，建议优先保留：

- `BackendProductCard` 的 `gift_role` 展示。
- `GiftSolutionPage`。
- `/gift-solution` 入口。

### 2. `backend/app/services/recommendation_service.py`

这是推荐主链路，冲突时要谨慎。

本轮关键逻辑：

- 画像负反馈过滤。
- 约束放宽分析。
- 预算优化方案生成。
- 方案裁判选择。
- `gift_role` 写入最终商品。
- pipeline 输出方案观测字段。

合并时不要丢失：

```text
ConstraintRelaxationService
BudgetOptimizerService
PlanJudgeService
selected_plan
gift_role
needs_relaxation
relaxation_options
```

### 3. `backend/app/services/chat_service.py`

本轮关键逻辑：

- 算法链路注入候选商品白名单。
- 注入 `selected_plan` 方案上下文。
- 直接大模型链路不注入候选商品，避免污染 `/compare`。
- 流式返回 `relaxation_options` 和带 `gift_role` 的 `product_cards`。

### 4. `backend/app/schemas/recommendation.py`

本轮新增了多组响应字段：

- `RelaxationOption`
- `RecommendationPlan`
- `plans`
- `selected_plan_id`
- `selected_plan_type`
- `plan_judge_reason`

这些字段被前端和评测依赖，合并时不能轻易删。

### 5. `backend/app/schemas/gift_intent.py`

预算语义字段非常关键：

```text
budget_constraint_type
budget_flexibility
budget_upper_bound
budget_reason
```

其中 `budget_upper_bound` 应由后端根据类型确定性计算，不能完全信任 LLM 返回的数值。

### 6. API 路由

新增路由：

```text
/api/gift-solution/generate
```

对应文件：

```text
backend/app/api/routes/gift_solution.py
backend/app/api/router.py
frontend/src/api/giftSolution.ts
```

## 验证记录

本轮开发中已跑过的验证：

```text
cd backend
python -m compileall app
```

```text
cd frontend
npm run build
```

服务/API 样例验证：

- `一个简单点的生日礼物，预算300`
  - 形态：`single_gift`
  - 返回 1 个 `main_gift`
- `第一次见家长，预算3000，体面点`
  - 形态：`gift_combo`
  - 返回 `main_gift + addon_gift`
- `预算500左右，可以再加一点，想搭配一套`
  - 形态：`gift_combo`
  - 返回 `main_gift + addon_gift`
- `POST /api/gift-solution/generate`
  - 三个样例均返回 200
  - 响应包含送礼话术、时机、地点、包装建议、推辞回应、避坑提醒

## 建议 commit 信息

如果这次作为一个大提交，可以使用：

```text
feat: upgrade gift recommendation to solution planning
```

如果拆成多个提交，建议：

```text
feat: add constraint relaxation for recommendations
feat: add budget optimized recommendation plans
feat: support budget semantics and gift roles
feat: expose gift solution generation flow
docs: add recommendation R11-R15 specs and merge notes
```

## 合并策略建议

如果后续和别人仓库 merge：

1. 先合后端 schema 和 service。
2. 再合 API routes。
3. 再合前端 api 类型。
4. 最后合 `AppPages.tsx` 页面改动。

原因：

- 后端 schema/service 是能力基础。
- 前端页面冲突概率最大，最后处理能减少返工。
- 如果页面冲突严重，至少先保证 `/api/gift-solution/generate` 和 `/api/products/recommendations` 可用。
