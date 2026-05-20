# 京礼推荐算法与 AI Agent 三阶段路线图

本目录把“从 Demo 级 RAG 导购，升级到第三阶段 Agent 导购推荐系统”的目标拆成可执行规约任务。

核心原则：

- 推荐算法负责“选商品”和“排序”。
- 大模型负责“理解用户意图”“追问澄清”“解释推荐”“辅助精排”。
- 商品卡片必须来自后端可控商品库，不能让大模型凭空生成。
- 每个阶段都要能独立上线，不依赖一次性重构。

## 三阶段目标

### 阶段一：结构化意图 + 规则推荐

目标：让系统从“LLM 自己挑商品”升级为“LLM 解析意图，后端算法选商品”。

任务：

1. [送礼意图结构化抽取](./01-gift-intent-extraction.md)
2. [商品规则打分器 V1](./02-product-scoring-v1.md)
3. [推荐管线 V1：召回、打分、排序、返回](./03-recommendation-pipeline-v1.md)
4. [基于候选商品的 AI 解释生成](./04-grounded-llm-explanation.md)

### 阶段二：语义召回 + 可解释精排

目标：引入向量召回和更稳定的排序特征，让推荐结果更准、更可解释。

任务：

5. [向量召回与混合召回](./05-vector-hybrid-retrieval.md)
6. [LLM Rerank 候选商品精排](./06-llm-rerank.md)
7. [推荐理由与打分证据结构化](./07-recommendation-evidence.md)

### 阶段三：多轮 Agent 导购

目标：系统能判断信息是否不足、主动追问，并结合用户画像持续优化推荐。

任务：

8. [多轮澄清与追问策略](./08-clarification-policy.md)
9. [用户画像与会话记忆](./09-user-profile-memory.md)
10. [推荐评测、观测与迭代闭环](./10-evaluation-observability.md)
11. [约束放宽与候选不足协商策略](./11-constraint-relaxation-policy.md)
12. [预算约束组合优化与方案裁判](./12-budget-optimized-plan-judge.md)
13. [预算约束语义化与主副礼组合建模](./13-budget-semantics-main-addon-plan.md)
14. [主副礼方案解释与前端展示](./14-plan-explanation-ui.md)
15. [礼物形态决策与完整送礼方案](./15-gift-shape-decision-solution.md)
16. [单品 Top3 与组合方案双流程](./16-single-vs-combo-recommendation-flow.md)

## 推荐执行顺序

先做 1-4，形成可控推荐闭环；再做 5-7，提升召回和排序质量；最后做 8-10，让 Agent 具备更完整的导购能力。

## 当前项目基础

项目已有基础能力：

- 商品 seed 数据已标准化到 `scenarios / target_people / budget_level / avoid_for / tags` 等字段。
- `RecommendationService` 已统一商品卡片构建、预算过滤和兜底商品。
- 前端已经可以展示 AI 文本和商品卡片。
- 礼单和购物车已经有后端接口和 SQLite 持久化。

因此下一步不应该继续让 LLM “直接推荐商品”，而应该建设可控推荐管线。
