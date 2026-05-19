# 任务 R5：向量召回与混合召回

## 目标

引入语义召回，解决用户表达和商品字段不完全一致时召回不足的问题。

## 范围

需要实现：

- 为商品构建 embedding 文本。
- 支持语义向量召回 Top K。本阶段不接外部向量库，先用本地可替换的语义 token 向量与余弦相似度实现，后续可替换为真实 embedding provider。
- 与字段召回、关键词召回合并。
- 对重复商品去重。

不做：

- 不训练 embedding 模型。
- 不依赖单一向量召回作为最终排序。

## 混合召回策略

```text
candidates =
  structured_recall(intent)
  ∪ keyword_recall(query)
  ∪ vector_recall(query_embedding)
```

## 建议文件

```text
backend/app/services/retrieval_service.py
backend/app/rag/embedder.py
backend/app/rag/store.py
```

## 当前实现约束

- 当前知识库是进程内 `KnowledgeStore`，关键词检索已经可用。
- 当前 embedding client 是 mock/占位实现，不能依赖真实外部向量服务。
- R5 先新增独立 `RetrievalService`，让推荐主流程调用混合召回结果。
- 语义召回只负责扩大候选集，不负责最终排序；最终排序仍由 R2 的 `ProductScorer` 完成。
- 语义召回异常时需要降级为空列表，不能影响结构化召回和关键词召回。

## 验收标准

- “有面子但别太贵”这类模糊表达也能召回相关商品。
- 向量召回结果不直接决定最终排序，仍进入 scorer。
- 向量服务不可用时，字段召回仍可工作。

## 风险点

- 向量召回容易带来噪声，需要后续规则打分过滤。
- embedding 文本必须包含场景、人群、禁忌和卖点。
- 本地语义向量只能覆盖 demo 级表达，不能等同真实大规模 embedding 检索。

## 执行记录

- 状态：已完成
- 规约更新：
  - 明确 R5 本阶段不接外部向量库和真实 embedding provider。
  - 明确采用本地可替换的语义 token 向量与余弦相似度实现 demo 级语义召回。
  - 明确语义召回只扩大候选集，最终排序仍交给 R2 `ProductScorer`。
- 实现内容：
  - 新增 `backend/app/services/retrieval_service.py`。
  - `RetrievalService.hybrid_recall()` 同时返回关键词知识库切片和语义商品候选。
  - 商品 embedding 文本覆盖品牌、名称、品类、预算档位、场景、人群、标签、卖点、评价摘要、禁忌和知识库文本。
  - 语义召回对“面子、别太贵、性价比、正式、健康、实用、颜值”等常见送礼表达做别名扩展。
  - `RecommendationService` 接入混合召回，将结构化召回、关键词召回、语义召回合并去重后统一进入 scorer。
  - 返回 `pipeline.semantic_recall_count`，方便前端/调试观察语义召回是否生效。
  - `hybrid_recall()` 对语义召回异常做降级，保证字段召回和关键词召回仍可工作。
- 验证结果：
  - `python -m compileall app` 通过。
  - 使用 “见家长送礼，有面子但别太贵，预算3000” 验证：
    - seed 商品数：50。
    - 语义召回 Top 结果包含围巾礼盒、燕窝礼盒、茶礼盒、香薰礼盒等。
    - 推荐结果返回龙井茶礼盒、金骏眉红茶礼罐、燕窝礼盒、山羊绒围巾礼盒。
    - pipeline：`structured_recall_count=2`、`knowledge_recall_count=2`、`semantic_recall_count=5`、`candidate_count=7`、`returned_count=4`。
  - 强制语义召回异常验证：
    - 推荐仍返回龙井茶礼盒、金骏眉红茶礼罐。
    - pipeline：`semantic_recall_count=0`，结构化召回和关键词召回继续工作。
- 后续建议：
  - R6 可进入 LLM rerank/解释生成：让大模型只在候选商品白名单内做重排和推荐话术，不再直接自由选品。
  - 后续接真实 embedding provider 时，优先替换 `RetrievalService.semantic_recall()`，保持推荐主流程稳定。
