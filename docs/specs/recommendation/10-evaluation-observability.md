# 任务 R10：推荐评测、观测与迭代闭环

## 目标

建立推荐质量评测和线上调试能力，让算法迭代有依据。

## 范围

需要实现：

- 固定评测集。
- 推荐结果快照。
- 核心指标日志。
- 用户反馈入口。
- 支持按推荐策略运行评测：`llm_direct / hybrid_algorithm / llm_rerank`。
- 评测结果能返回每个 case 的 Top N 商品、pipeline、intent 和命中情况。

不做：

- 不做完整 AB 实验平台。
- 不调用真实支付/结算链路统计商业转化。

## 建议指标

- 召回商品数量
- Top N 场景匹配率
- 预算命中率
- 禁忌误推率
- 加入礼单率
- 结算预览率

## 建议评测样例

```text
给女朋友生日礼物，预算500
第一次见家长，预算3000，体面点
送领导，不想太冒犯
乔迁礼物，实用一点
探望长辈，健康相关
```

## 验收标准

- 每次推荐能记录 intent、候选数、Top N、排序来源。
- 有一组可重复跑的评测 case。
- 改排序权重后能比较前后结果。
- `/api/eval/run` 能运行推荐评测并返回聚合指标。
- `/api/eval/results` 能看到最近推荐评测快照。

## 风险点

- 指标不能只看点击率，送礼场景还要看“合适”和“分寸”。
- 评测集要覆盖边界场景和禁忌场景。

## 当前实现约束

- 当前已有 `MetricsCollector`，但主要记录聊天 citation/feedback 指标。
- R10 先扩展进程内评测指标，不引入数据库。
- 为避免评测依赖真实大模型不稳定，评测时可传入 `gift_intent` 或使用规则抽取，保证结果可重复。
- 评测 case 先关注推荐管线：
  - 是否需要追问。
  - 是否返回商品。
  - Top N 是否命中目标场景/对象/预算。
  - 是否误推禁忌商品。
  - 是否重复推荐。

## 执行记录

- 状态：已完成
- 规约更新：
  - 明确 R10 支持按推荐策略运行评测：`llm_direct / hybrid_algorithm / llm_rerank`。
  - 明确评测结果需要返回每个 case 的 Top N 商品、pipeline、intent 和命中情况。
  - 明确本阶段不做完整 AB 平台，也不接真实支付/结算转化。
  - 明确 Demo 阶段使用进程内评测指标，不引入数据库。
- 实现内容：
  - 更新 `backend/app/schemas/eval.py`：
    - `EvalRunResponse` 增加 `metrics` 与 `cases`，用于返回聚合指标和逐 case 快照。
  - 更新 `backend/app/metrics/collector.py`：
    - 新增 `RecommendationEvalRecord`。
    - 新增 `record_recommendation_eval()`。
    - `snapshot()` 增加 `recommendation_eval_total` 与 `recommendation_eval_summary`。
    - 新增 `recent_recommendation_evals()`，用于 `/api/eval/results` 返回最近推荐评测记录。
  - 重写 `backend/app/services/eval_service.py`：
    - 新增 6 条固定推荐评测 case：
      - 女朋友生日礼物，预算 500。
      - 第一次见家长，预算 3000，体面点。
      - 送领导，不想太冒犯。
      - 乔迁礼物，实用一点。
      - 探望长辈，健康相关。
      - 模糊输入“推荐个礼物”，应触发追问。
    - 评测时使用结构化 `GiftIntent`，降低真实 LLM 波动对评测的影响。
    - 每个 case 返回 Top N 商品、intent、pipeline 与检查项。
    - 聚合指标包括：
      - `scenario_hit_rate`
      - `target_hit_rate`
      - `budget_hit_rate`
      - `avoid_violation_rate`
      - `clarification_accuracy`
      - `duplicate_case_rate`
      - `avg_returned_count`
  - 更新 `backend/app/api/routes/eval.py`：
    - `POST /api/eval/run?strategy=hybrid_algorithm` 支持通过 query 参数指定策略。
    - `GET /api/eval/results` 返回最近推荐评测快照。
- 验证结果：
  - `python -m compileall app` 通过。
  - 服务级验证 `EvalService().run(strategy="hybrid_algorithm")`：
    - `executed=6`。
    - `failures=0`。
    - 返回 6 条 case 快照。
    - 聚合指标：
      - `scenario_hit_rate=0.6667`
      - `target_hit_rate=1.0`
      - `budget_hit_rate=1.0`
      - `avoid_violation_rate=0.0`
      - `clarification_accuracy=1.0`
      - `duplicate_case_rate=0.0`
      - `avg_returned_count=2.67`
  - 服务级验证 `EvalService().summary()`：
    - `status=ready`。
    - `recommendation_eval_total=6`。
    - `recent` 返回最近推荐评测记录。
  - API 验证：
    - `POST /api/eval/run?strategy=hybrid_algorithm` 返回 200。
    - `executed=6`、`failures=0`、`cases=6`。
    - `GET /api/eval/results` 返回 200。
    - `status=ready`，并包含 `recommendation_eval_summary`。
- 当前发现：
  - `送领导，不想太冒犯` 和 `探望长辈，健康相关` 的对象、预算、禁忌检查通过，但 `scenario_hit=False`。
  - 这说明当前商品数据或召回标签对“送领导/客户”“探望长辈”场景覆盖不足，是下一轮数据和召回优化的明确方向。
- 后续建议：
  - 扩充 seed 商品的 `scenarios` 标签，特别是“送领导/客户”“探望长辈”。
  - 把 R10 评测作为每次调整 scorer 权重、召回策略、商品数据后的回归检查。
  - 后续可增加导出 JSON 快照，方便比较不同 commit 或不同策略的评测结果。
