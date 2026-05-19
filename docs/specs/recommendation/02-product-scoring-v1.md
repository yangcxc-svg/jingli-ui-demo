# 任务 R2：商品规则打分器 V1

## 目标

建立一个可解释的规则打分器，让商品推荐不再只靠大模型或关键词命中。

## 范围

需要实现：

- 新增 `ProductScorer`。
- 基于 `GiftIntent` 对商品打分。
- 输出总分和分项证据。
- 支持禁忌惩罚。
- 接入 `RecommendationService`，让推荐结果携带商品打分证据。

不做：

- 不引入机器学习训练。
- 不做复杂个性化。

## 建议打分项

```text
总分 =
  场景匹配分
  + 人群匹配分
  + 预算匹配分
  + 偏好标签匹配分
  + 热度/评分分
  - 禁忌惩罚
```

## 建议数据结构

```py
class ProductScore(BaseModel):
    product_id: str
    score: float
    reasons: list[str]
    penalties: list[str] = []
```

## 建议文件

```text
backend/app/services/product_scorer.py
backend/app/schemas/recommendation_score.py
```

## 本轮实施边界

当前项目已经完成 R1：

- `GiftIntent` 可以抽取送礼对象、场景、预算、偏好和禁忌。
- `RecommendationService` 已经统一商品卡片构建。

因此本轮实现：

- `ProductScorer` 接收 `GiftIntent` 和商品原始 dict，输出 `ProductScore`。
- `RecommendationService` 在返回商品前对候选商品打分并排序。
- `RecommendationResult` 增加 `scores` 字段，保留每个推荐商品的打分证据。
- 暂不改变前端展示，证据先给 R3/R4 和调试使用。

## 验收标准

- 符合场景和人群的商品分数高于不相关商品。
- 超预算商品被降权或过滤。
- `avoid_for` 命中时有明确惩罚原因。
- 每个推荐商品至少有 1 条可展示的推荐依据。

## 风险点

- 规则权重不要硬编码散落在多个文件，建议集中配置。
- 分数不是最终答案，后续还会接 rerank。

## 本轮执行记录

已完成：

- 新增 `backend/app/schemas/recommendation_score.py`：
  - 定义 `ProductScore`
  - 字段包含 `product_id / score / reasons / penalties`
- 新增 `backend/app/services/product_scorer.py`：
  - 定义 `ProductScorer`
  - 定义集中权重 `ProductScoringWeights`
  - 支持场景匹配、人群匹配、预算匹配、偏好命中、风格命中、评价加分、禁忌惩罚、超预算惩罚
- 更新 `backend/app/schemas/recommendation.py`：
  - `RecommendationResult` 增加 `scores`
- 更新 `backend/app/services/recommendation_service.py`：
  - 候选商品会被 `ProductScorer` 打分
  - 推荐商品按分数降序返回
  - 返回结果携带每个商品的打分证据
  - 修正预算过滤逻辑，明显超出预算 15% 的商品不会作为首个候选直接放行

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

规则打分验证：

```text
MATCHED 100.0
reasons=['匹配送礼场景：生日', '适合送礼对象：女生', ...]
penalties=[]

UNMATCHED 0.0
penalties=['明显超出预算']

AVOID 51.0
penalties=['禁忌命中：女生']
```

推荐服务验证：

```text
输入：想给25岁女生送生日礼物，预算500元。
输出：返回商品数量 > 0，且 scores 与 products 对齐。

输入：见家长，预算3000，体面点
输出：返回商品数量 > 0，且 RecommendationResult.intent 正常保留。
```

接口验证：

- `POST /api/gift-plan/generate` 返回 200
- `POST /api/chat/stream` 返回 200

后续可继续做：

- R3 将候选召回、打分、排序整理成更明确的推荐管线。
- 增加自动化单测覆盖 `ProductScorer` 的场景匹配、人群匹配、预算惩罚、禁忌惩罚。
- 商品数据需要继续补充更贴近送礼语义的 `scenarios / target_people / tags`，否则部分真实 case 只能靠放宽召回兜底。
