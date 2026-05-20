# 任务 R13：预算约束语义化与主副礼组合建模

## 背景

R12 已经引入“方案层”：同一批候选商品可以生成 `ranked_topn` 和 `budget_optimized` 两类方案，再由规则裁判选择最终返回方案。

但 R12 的预算约束仍然偏机械：只要识别到 `budget=500`，优化器就把 500 当成固定上限。真实用户表达里，预算强度并不一样：

- “500 以内 / 不超过 500 / 最多 500”：这是硬约束。
- “500 左右 / 大概 500 / 差不多 500”：这是软约束。
- “500，可以再加一点 / 先按 500 看”：这是可协商约束。

同时，R12 的组合优化虽然有多样性和互补性分数，但还没有显式表达“主礼 + 副礼”的组合结构。真实导购推荐组合时，用户应该能理解哪个是主礼、哪个是补充礼，而不是看到几个商品被简单凑在一起。

## 目标

让预算优化从“固定金额过滤”升级为“理解用户预算表达强度后的约束优化”，并让组合推荐具备明确的主副礼结构。

理想效果：

```text
用户：预算 500 以内
系统约束：total_price <= 500

用户：预算 500 左右
系统约束：total_price <= 575 或 650，并对超出 500 的部分加惩罚

用户：预算 500，可以再加一点
系统约束：total_price <= 650，并允许选择能明显提升体验的方案
```

组合结构示例：

```json
{
  "plan_type": "budget_optimized",
  "product_ids": ["PROD-WATCH-001", "PROD-HEALTH-001"],
  "gift_roles": {
    "PROD-WATCH-001": "main_gift",
    "PROD-HEALTH-001": "addon_gift"
  },
  "judge_reason": "以智能手表作为主礼，维生素礼盒作为健康补充礼，组合更完整"
}
```

## 范围

需要实现：

- 在送礼意图中新增预算语义字段：
  - `budget_constraint_type`: `hard | soft | negotiable | unknown`
  - `budget_flexibility`: 预算允许浮动比例。
  - `budget_upper_bound`: 推荐优化可使用的预算上限。
  - `budget_reason`: 解释预算约束来源。
- 意图抽取支持预算表达强度：
  - 规则抽取识别“以内 / 不超过 / 最多 / 上限”等硬约束。
  - 规则抽取识别“左右 / 大概 / 差不多 / 上下”等软约束。
  - 规则抽取识别“可以加一点 / 可加 / 能加 / 放宽”等可协商约束。
  - LLM 抽取 prompt 同步 schema。
- 优化器使用语义预算：
  - 用 `budget_upper_bound` 作为组合枚举上限。
  - 用原始 `budget` 计算预算利用率。
  - 对超过原始预算但未超过上限的方案施加软惩罚。
- 显式建模主副礼：
  - `RecommendationPlan` 增加 `gift_roles`。
  - 组合方案根据价格、分数和位置标记 `main_gift / addon_gift`。
  - 互补性分数显式参考主副礼结构。
- 评测输出预算语义和主副礼结构。

不做：

- 不让 LLM 自由写 Python/SQL/数学约束。
- 不引入复杂求解器。
- 不改前端 UI 展示主副礼，初版先在接口和评测中可观测。
- 不突破用户明确的硬约束。

## 预算语义规则

初版规则：

```text
hard:
  关键词：以内、不超过、别超过、最多、上限、封顶
  flexibility = 0
  upper_bound = budget

soft:
  关键词：左右、大概、差不多、上下、附近
  flexibility = 0.15
  upper_bound = budget * 1.15

negotiable:
  关键词：可以再加一点、可加一点、能加一点、预算可以加、放宽
  flexibility = 0.30
  upper_bound = budget * 1.30

unknown:
  用户只说“预算 500”
  flexibility = 0.15
  upper_bound = budget * 1.15
```

说明：

- `unknown` 保留当前系统“略超预算可确认”的策略，但比 `hard` 更宽松。
- 超过原始预算的组合必须在方案分数中受到惩罚。
- 如果最终选择超出原始预算的方案，回复层后续应说明“略超原预算”。

## 主副礼规则

初版规则：

- 单品方案：该商品为 `main_gift`。
- 多品方案：
  - 分数和价格综合最高的商品为 `main_gift`。
  - 其余商品为 `addon_gift`。
- 如果主礼价格明显高于副礼，且副礼品类/标签和主礼不同，则提高 `complement_score`。
- 如果多个商品价格和品类高度相似，则降低互补性。

## 建议文件

```text
backend/app/schemas/gift_intent.py
backend/app/agent/prompts_lib/intent_extraction.py
backend/app/services/intent_extractor.py
backend/app/schemas/recommendation.py
backend/app/services/budget_optimizer_service.py
backend/app/services/plan_judge_service.py
backend/app/services/recommendation_service.py
backend/app/services/eval_service.py
docs/specs/recommendation/README.md
```

## 验收标准

- “预算 500 以内”抽取为 `hard`，优化组合总价不超过 500。
- “预算 500 左右”抽取为 `soft`，优化器允许在上限内小幅超过 500，但有惩罚。
- “预算 500，可以再加一点”抽取为 `negotiable`，优化器允许更高上限，但仍不能无限放大。
- `RecommendationResult.plans` 中能看到 `budget_upper_bound / budget_constraint_type / gift_roles`。
- 多商品组合能标记一个 `main_gift` 和至少一个 `addon_gift`。
- 后端编译、推荐服务样例、评测和前端 build 通过。

## 风险点

- 当前商品库较小，预算浮动不一定总能找到更优组合。
- 软预算如果惩罚过轻，会让系统频繁超预算。
- 主副礼初版依赖价格和分数推断，后续最好在商品库中补充更明确的 `gift_role_hint`。

## 执行记录

- 状态：已完成
- 规约更新：
  - 明确 R13 同时包含两个能力：预算约束语义化、主副礼组合显式建模。
  - 明确 LLM/规则只负责判断预算约束类型，具体浮动比例和预算上限由后端确定性规则计算。
  - 明确初版不改前端 UI，先保证接口和评测可观测。
- 实现内容：
  - 更新 `backend/app/schemas/gift_intent.py`：
    - 新增 `BudgetConstraintType`。
    - `GiftIntent` 新增 `budget_constraint_type / budget_flexibility / budget_upper_bound / budget_reason`。
    - 后端根据约束类型确定性计算预算浮动和上限：
      - `hard`: 0%，上限等于原预算。
      - `soft`: 15%，上限为原预算 1.15 倍。
      - `negotiable`: 30%，上限为原预算 1.30 倍。
      - `unknown`: 15%，沿用略超预算可确认策略。
  - 更新 `backend/app/agent/prompts_lib/intent_extraction.py`：
    - 意图抽取 prompt 增加预算约束类型说明和 schema 字段。
  - 更新 `backend/app/services/intent_extractor.py`：
    - 规则抽取支持硬预算、软预算、可协商预算关键词。
    - 合并 LLM 与规则结果时，如果 LLM 预算类型为 `unknown`，使用规则侧更明确的类型。
  - 更新 `backend/app/schemas/recommendation.py`：
    - `RecommendationPlan` 新增：
      - `original_budget`
      - `budget_upper_bound`
      - `budget_constraint_type`
      - `upper_bound_usage`
      - `budget_overage`
      - `budget_overage_ratio`
      - `gift_roles`
  - 更新 `backend/app/services/budget_optimizer_service.py`：
    - 组合枚举使用 `budget_upper_bound` 作为可行上限。
    - 预算利用分使用上限预算，超出原预算但未超过上限时单独加软惩罚。
    - 多商品方案显式标记 `main_gift / addon_gift`。
    - 互补性分数参考主副礼价格结构和品类差异。
  - 更新 `backend/app/services/recommendation_service.py`：
    - 推荐管线向优化器传入完整 `GiftIntent`。
    - 候选召回阶段使用语义预算上限，硬预算不再被默认 15% 放宽。
    - pipeline 增加预算约束类型、预算上限、超预算比例等观测字段。
  - 更新 `backend/app/services/plan_judge_service.py`：
    - 如果默认方案超过预算上限，而优化方案在预算上限内，优先选择优化方案。
  - 更新 `backend/app/services/eval_service.py`：
    - 增加硬预算和可协商预算组合 case。
    - case 输出包含预算语义、预算上限、超预算比例和主副礼角色。
- 验证结果：
  - 意图规则抽取验证：
    - `预算500以内` => `hard / flexibility=0 / upper_bound=500`。
    - `预算500左右` => `soft / flexibility=0.15 / upper_bound=575`。
    - `预算500，可以再加一点` => `negotiable / flexibility=0.30 / upper_bound=650`。
  - 服务级验证：
    - `给女朋友生日礼物，预算500以内，要有心意`：
      - `intent.budget_constraint_type=hard`。
      - `budget_upper_bound=500`。
      - 最终方案总价 456 元，不超过硬预算。
      - 多商品方案包含 `main_gift` 和 `addon_gift`。
    - `给女朋友生日礼物，预算500左右，要有心意`：
      - `intent.budget_constraint_type=soft`。
      - `budget_upper_bound=575`。
      - 默认方案 645 元超过上限，被裁判排除。
      - 选择 477 元预算优化方案。
    - `给女朋友生日礼物，预算500左右，可以再加一点，想搭配一套`：
      - `intent.budget_constraint_type=negotiable`。
      - `budget_upper_bound=650`。
      - 返回预算优化组合，并带主副礼角色。
  - API 验证：
    - `POST /api/products/recommendations` 返回 200。
    - 真实 LLM 抽取时即使返回了不一致的数值上限，后端也会按约束类型重新计算上限。
    - 响应中的 `plans` 包含 `gift_roles`。
  - 评测验证：
    - `EvalService().run(strategy="hybrid_algorithm")` 执行 9 条 case，失败 0 条。
    - 指标包含 `budget_optimized_selection_rate=0.4444`。
    - 指标包含 `avg_selected_budget_usage=0.9236`。
  - 编译与构建：
    - 后端 `python -m compileall app` 通过。
    - 前端 `npm run build` 通过。
- 当前发现：
  - 预算语义化后，硬预算 case 不再被旧逻辑默认放宽 15%。
  - `unknown` 预算仍保留 15% 浮动，这和当前导购体验比较一致，但后续可以通过评测决定是否改成更保守。
  - 主副礼目前仍由价格和分数推断，商品库缺少 `gift_role_hint`，因此角色标注还不是商品知识层面的强语义。
- 后续建议：
  - R14 可以补商品结构字段：`category_group / gift_role_hint / complement_with / occasion_weight`。
  - 前端可在商品卡片或方案摘要中展示“主礼 / 副礼”，让组合推荐更容易被用户理解。
  - 聊天回复 prompt 可读取 `gift_roles`，用自然语言说明“主礼是什么，副礼补充什么”。
