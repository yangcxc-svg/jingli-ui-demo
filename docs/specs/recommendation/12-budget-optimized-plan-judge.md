# 任务 R12：预算约束组合优化与方案裁判

## 背景

R1-R11 已经让推荐系统具备了结构化意图抽取、混合召回、规则打分、LLM 精排、用户画像、追问和约束放宽能力。

当前仍然存在一个明显问题：当用户表达“预算可以再加一点”“希望更健康一点”“换一个”等追问时，系统虽然能继续推荐真实商品，但推荐结果对“预算利用”和“组合价值”的理解还比较弱。

例如：

```text
用户：偏好健康一些的，预算可以再加一点
系统：可能仍推荐 298 元维生素，或者单独推荐 1580 元燕窝。
```

这不一定错，但没有体现“预算增加以后，是否能得到更好的方案”。一个更合理的导购系统应该能同时考虑：

- 商品相关度。
- 总预算约束。
- 商品数量约束。
- 场景和人群约束。
- 组合之间的互补性。
- 不要为了花完预算而牺牲匹配度。

因此 R12 引入“推荐方案层”：同一批候选商品不只生成一个 TopN 排序结果，还生成一个预算约束下的组合优化方案，再由方案裁判选择最终返回给用户的方案。

## 目标

让推荐系统从“选几个分数最高的商品”升级为“在预算和场景约束下选择更合理的推荐方案”。

理想效果：

```text
用户：送女朋友生日礼物，预算1500，偏健康一点

系统内部生成：
1. ranked_topn：按相关度排序的 TopN 商品。
2. budget_optimized：预算内价值更高的组合，例如智能手表 + 维生素礼盒。

方案裁判判断：
- 如果组合方案相关度接近 TopN，且预算利用更合理，则选择组合方案。
- 如果组合方案为了凑预算牺牲相关度，则继续选择 TopN。
```

## 范围

需要实现：

- 定义 `RecommendationPlan`：
  - `plan_id`
  - `plan_type`
  - `products`
  - `product_ids`
  - `total_price`
  - `budget_usage`
  - `relevance_score`
  - `diversity_score`
  - `complement_score`
  - `objective_score`
  - `judge_reason`
- 新增预算优化服务：
  - 从已召回并打分的候选中枚举 1-N 个商品组合。
  - 过滤明显超预算组合。
  - 计算组合目标函数。
  - 返回最优组合方案。
- 新增方案裁判服务：
  - 同时接收 `ranked_topn` 和 `budget_optimized`。
  - 使用确定性规则选择最终方案。
  - 为后续 LLM 裁判保留接口，不在初版强依赖 LLM。
- 推荐结果返回方案信息：
  - `plans`
  - `selected_plan_id`
  - `selected_plan_type`
  - `plan_judge_reason`
- 更新评测观测：
  - 记录预算利用率。
  - 记录选择了哪类方案。
  - 观察组合优化是否改善预算表达场景。

不做：

- 不引入 OR-Tools 等重型求解器。
- 不做跨店铺、库存、运费、优惠券等电商复杂约束。
- 不让 LLM 直接决定最终商品白名单。
- 不为了花完预算而推荐低相关商品。

## 初版目标函数

初版采用轻量组合枚举，不需要外部依赖。

```text
objective =
  0.55 * relevance_score
+ 0.20 * budget_usage_score
+ 0.15 * diversity_score
+ 0.10 * complement_score
- penalties
```

说明：

- `relevance_score`：组合中商品规则得分的归一化结果，保证核心仍是匹配用户需求。
- `budget_usage_score`：预算利用率，鼓励合理使用预算，但不强迫花完。
- `diversity_score`：品类、标签、卖点有一定差异，避免推荐一组太重复的商品。
- `complement_score`：简单判断组合是否能形成“主礼 + 补充礼”。
- `penalties`：超预算、商品数过多、重复品类过高等惩罚。

## 方案裁判规则

初版优先使用确定性规则：

1. 如果用户明确说“组合 / 礼单 / 搭配”，优先考虑 `budget_optimized`。
2. 如果 `ranked_topn` 预算利用率很低，而 `budget_optimized` 相关度接近且预算利用明显更好，选择 `budget_optimized`。
3. 如果 `budget_optimized` 相关度明显低于 `ranked_topn`，选择 `ranked_topn`。
4. 如果两者差距不明显，选择目标函数更高的方案。

后续可扩展为：

```text
规则裁判先筛掉明显不合理方案；
LLM 裁判只在两个方案都合理且差距不明显时，阅读结构化理由后选择更适合用户表达的方案。
```

## 建议文件

```text
backend/app/schemas/recommendation.py
backend/app/services/budget_optimizer_service.py
backend/app/services/plan_judge_service.py
backend/app/services/recommendation_service.py
backend/app/services/eval_service.py
docs/specs/recommendation/README.md
```

## 验收标准

- 推荐接口在正常返回商品时，同时返回 `plans` 和被选中的 `selected_plan_type`。
- 当用户有明确预算时，`budget_optimized` 不返回明显超预算组合。
- 当组合方案相关度接近且预算利用明显更好时，最终结果可以选择 `budget_optimized`。
- 当组合方案为了凑预算导致相关度明显下降时，最终结果仍选择 `ranked_topn`。
- 评测输出能看到：
  - `selected_plan_type`
  - `budget_usage`
  - `plan_judge_reason`
- 后端编译和评测接口通过。

## 风险点

- 当前商品库较小，优化器可能受限于候选不足，效果不会总是明显。
- 预算利用率不能成为唯一目标，否则会把“不合适但贵”的商品推上来。
- 商品组合的互补性初版只能用类目和标签粗略估计，后续需要更结构化的商品属性。
- 如果用户只想要一个主礼，组合方案不应过度出现。

## 执行记录

- 状态：已完成
- 规约更新：
  - 新增 R12 文档，明确本任务是“方案层”能力，不替换现有召回、打分、Rerank。
  - 初版采用轻量组合枚举，不引入 OR-Tools 等重型求解器。
  - 明确规则裁判优先，LLM 裁判作为后续可扩展能力。
- 实现内容：
  - 更新 `backend/app/schemas/recommendation.py`：
    - 新增 `RecommendationPlanType`。
    - 新增 `RecommendationPlan`。
    - `RecommendationResult` 新增 `plans / selected_plan_id / selected_plan_type / plan_judge_reason`。
    - `pipeline` 支持浮点型观测字段。
  - 新增 `backend/app/services/budget_optimizer_service.py`：
    - 基于已召回、已打分候选商品生成 `ranked_topn` 默认方案。
    - 枚举预算内 1-N 个商品组合，生成 `budget_optimized` 方案。
    - 计算相关度、预算利用、多样性、互补性和综合目标函数。
  - 新增 `backend/app/services/plan_judge_service.py`：
    - 根据用户是否表达组合需求、预算利用率、相关度差距和目标函数选择最终方案。
    - 保留后续接入 LLM 裁判的清晰接口边界。
  - 更新 `backend/app/services/recommendation_service.py`：
    - 在 `ranked_all` 之后生成候选方案。
    - 由方案裁判选择最终返回商品。
    - 将方案选择结果写入响应和 pipeline。
  - 更新 `backend/app/services/eval_service.py`：
    - case 结果新增方案列表、选中方案、预算利用率和裁判理由。
    - 汇总指标新增 `budget_optimized_selection_rate / avg_selected_budget_usage`。
  - 更新 `docs/specs/recommendation/README.md`：
    - 将 R12 加入阶段三任务列表。
- 验证结果：
  - 后端 `python -m compileall app` 通过。
  - 服务级验证 1：
    - 输入 `送女朋友生日礼物，预算1500，偏健康一点，想要搭配一套`。
    - 返回 `selected_plan_type=ranked_topn`。
    - 方案总价 1136 元，预算利用率约 0.7573。
  - 服务级验证 2：
    - 输入 `给女朋友生日礼物，预算500，要有心意`。
    - 同时生成 `ranked_topn` 和 `budget_optimized`。
    - `ranked_topn` 总价 556 元，超过 500 元总预算。
    - `budget_optimized` 选择 388 元单品，预算利用率约 0.776。
    - 最终返回 `selected_plan_type=budget_optimized`。
  - API 验证：
    - `POST /api/products/recommendations` 返回 200。
    - 响应包含 `selected_plan_type / plan_judge_reason / plans / pipeline.selected_plan_budget_usage`。
  - 评测验证：
    - `EvalService().run(strategy="hybrid_algorithm")` 执行 7 条 case，失败 0 条。
    - 指标包含 `budget_optimized_selection_rate=0.7143`。
    - 指标包含 `avg_selected_budget_usage=0.7399`。
  - 前端 `npm run build` 通过。
- 当前发现：
  - R12 已经能避免“单品都不超预算，但组合总价超预算”的问题。
  - 当前商品库较小，优化器有时会选择 1 个商品而不是多个商品，这是符合预算约束的结果，但体验上后续可增加“期望商品数量”或“主礼/副礼”偏好。
  - `budget_optimized_selection_rate` 初版偏高，后续可以通过评测集继续调裁判阈值。
- 后续建议：
  - R13 可加入“主礼 + 副礼”结构化组合策略，避免组合优化只从分数和价格推断互补性。
  - 增加更丰富的健康类、轻奢类、实用类商品，才能更明显体现预算增加后的推荐质量提升。
  - 视效果再接入 LLM 裁判，但应保持“规则先过滤，LLM 只做难例判断”的边界。
