# 任务 5：知识库与商品数据升级

> 说明：本任务主要覆盖商品 schema 与知识库数据基础。若目标升级为“第三阶段 Agent 导购推荐系统”，请继续查看专题规约：[推荐算法与 AI Agent 三阶段路线图](./recommendation/README.md)。

## 目标

把当前种子商品数据升级成更稳定的商品知识库，让推荐结果更准确、更可解释。

## 当前问题

- 商品数据字段还偏简单。
- 推荐依赖关键词检索，语义和场景匹配能力有限。
- 缺少数据校验和加载失败提示。

## 范围

需要实现：

- 统一商品 schema。
- 增加场景、人群、预算、禁忌、卖点、图片、购买链接等字段。
- 后端启动时校验商品数据。
- 增加商品数据加载和校验脚本。
- 为推荐服务提供更强的过滤条件。

不做：

- 不接真实商品平台 API。
- 不建设复杂后台管理系统。

## 建议商品字段

```json
{
  "product_id": "string",
  "name": "string",
  "price": 1299,
  "image_url": "string",
  "purchase_url": "string",
  "target_people": ["长辈", "女生", "客户"],
  "scenarios": ["见家长", "生日", "乔迁"],
  "budget_level": "mid",
  "tags": ["体面", "实用"],
  "highlights": ["核心卖点"],
  "avoid_for": ["关系不熟", "预算过低"],
  "description": "string"
}
```

## 验收标准

- 商品数据不符合 schema 时，后端启动或校验命令能报出明确错误。
- 推荐服务可以按预算、场景、人群过滤商品。
- 前端商品卡片字段完整，不出现空标题、空价格。
- README 说明如何更新商品数据。

## 风险点

- 字段越多越容易不一致，必须先有校验。
- 图片链接如果不可访问，前端需要兜底图。

## 本轮执行记录

已完成：

- 新增 `backend/app/schemas/seed_product.py`：统一 seed 商品 schema，必填 `product_id/name/category`，`price` 非负，`image_url/purchase_url` 校验为合法 URL 或本地路径，`budget_level` 按价格自动推导（可被 JSON 覆盖），并将老字段 `use_cases/target_users/not_recommended_for/comparison_tags` 映射到新字段 `scenarios/target_people/avoid_for/tags`。
- 改造 `backend/app/services/seed_product_loader.py`：启动期严格校验，任一不合法字段或 `product_id` 重复都会以 `SeedProductValidationError` 抛出明确错误；知识检索文本也注入 `scenarios/target_people/budget_level/tags/avoid_for`。
- `backend/app/main.py` 的 `lifespan` 调用改为 `seed_product_catalog.load(strict=True)`。
- 扩展 `backend/app/schemas/product.py` 与 `backend/app/schemas/recommendation.py`：`ProductCard`/`ProductResponse` 增加 `scenarios/target_people/budget_level/avoid_for/highlights/purchase_url`；`RecommendationRequest` 增加 `scenarios/target_people/budget_level` 过滤维度。
- 改造 `backend/app/services/recommendation_service.py`：`build_product_cards` 与 `fallback_products` 接受场景、人群、预算等级过滤；`product_to_card` 同步透出新字段；`_build_query` 把过滤维度纳入检索 query。
- 改造 `backend/app/repositories/product_repo.py`：商品列表透出新字段，`tags` 优先级为 `tags > comparison_tags > use_cases`。
- 新增 CLI 校验脚本 `backend/app/scripts/validate_products.py`：`python -m app.scripts.validate_products` 通过返回 0 并打印商品数量、`budget_level` 分布；失败时返回非零并列出错误。
- 前端 `frontend/src/api/chat.ts` 的 `ProductCardData` 增加 `scenarios/target_people/budget_level/avoid_for`；`frontend/src/pages/AppPages.tsx` 的 `BackendProductCard` 接受 `http(s) / / ./` 三类图片路径并对空标题、空 `image_url` 提供兜底。
- README 增加“如何更新商品数据”章节，说明 schema、CLI 校验流程与图片兜底策略。

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

```bash
cd backend
python -m app.scripts.validate_products
# [ok] storage/sample_docs/seed_products.json
#   products: 30
#   budget_level distribution: {'low': 7, 'mid': 16, 'high': 7}
```

通过。

负向测试（构造 4 条非法商品）：

```text
products[0] (product_id=''): String should have at least 1 character
products[1] (product_id='A'): price must be non-negative
products[2] (product_id='A'): duplicate product_id 'A'
products[3] (product_id='B'): invalid url-like value: 'not-a-url'
```

四类错误均被精确定位。

使用 FastAPI `TestClient` 验证：

- `GET /api/products` 返回 200，30 件商品，响应字段包含 `scenarios/target_people/budget_level/avoid_for/highlights/purchase_url`。
- `RecommendationService.fallback_products(budget_level='low')` 返回 7 件且全部为 `low`。
- `RecommendationService.fallback_products(target_people=['学生党'])` 返回 10 件，过滤后所有商品 `target_people` 均命中。
- `RecommendationService.fallback_products(scenarios=['日常通勤'])` 返回 3 件，过滤后所有商品 `scenarios` 均命中。
- `recommend_products` 主路径在 budget=1500 + include_fallback=True 下正常返回商品卡片。

```bash
cd frontend
npm run build
```

通过（`tsc --noEmit` + `vite build` 均成功）。

后续可继续做：

- 把 schema 错误信息接入 `/api/health/ready`，让 readiness 也能反映 seed 数据状态。
- 给 `RecommendationService._matches_filters` 加单元测试，覆盖 budget_level / scenarios / target_people 三种过滤的边界。
- 引入更细的 `budget_level` 分级或将其改为可配置。
- 将 30 件商品逐条补充显式的 `scenarios`（如送礼场景：见家长 / 生日 / 乔迁 / 商务），覆盖比 `use_cases` 更贴近送礼语义的字段。
