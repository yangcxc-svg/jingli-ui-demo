# 任务 R14：主副礼方案解释与前端展示

## 背景

R12-R13 已经让推荐系统具备了“方案层”能力：

- 推荐服务会生成 `ranked_topn / budget_optimized` 等方案。
- 方案裁判会选择最终方案。
- `RecommendationPlan` 已包含预算语义、预算上限、超预算比例和 `gift_roles`。
- 多商品组合已经能标记 `main_gift / addon_gift`。

但这些能力目前主要停留在接口和评测层，用户在聊天界面里还感知不到：

- AI 回复没有稳定解释“为什么这是一个组合方案”。
- AI 回复没有明确说明哪个是主礼、哪个是副礼。
- 前端商品卡片没有展示“主礼 / 副礼”标识。
- 如果方案略超原始预算，回复没有稳定解释“为什么值得略超”。

因此 R14 的目标是把 R13 的结构化方案信息转化为用户能理解的导购表达。

## 目标

让最终推荐不只是返回商品卡片，而是形成一个可读、可信、可比较的送礼方案。

理想效果：

```text
我建议用「观夏 颐和金桂香薰礼盒」做主礼，它更适合作为生日场景下有心意、颜值高的核心礼物。
再搭配「茉莉精油扩香瓶」做副礼，补充日常使用感，整体仍控制在 500 元以内。
```

前端卡片展示：

```text
[主礼] 观夏 颐和金桂香薰礼盒
[副礼] 国民品牌 茉莉精油扩香瓶
```

如果预算可浮动：

```text
这套方案比原始 500 元预算略高，但仍在你说的“可以再加一点”的范围内，整体更完整。
```

## 范围

需要实现：

- 后端聊天链路传递方案上下文：
  - `selected_plan_type`
  - `plan_judge_reason`
  - `total_price`
  - `original_budget`
  - `budget_upper_bound`
  - `budget_constraint_type`
  - `budget_overage_ratio`
  - `gift_roles`
- Prompt 支持方案解释：
  - 说明推荐是单品方案还是组合方案。
  - 如果有 `main_gift`，说明为什么它适合作为主礼。
  - 如果有 `addon_gift`，说明副礼如何补充主礼。
  - 如果超过原始预算但未超过语义预算上限，必须温和说明原因。
  - 禁止输出不存在于候选商品列表中的商品。
- 商品卡片携带角色信息：
  - `ProductCard` 或接口响应中增加 `gift_role`。
  - 前端 `ProductCardData` 增加 `gift_role`。
  - 前端商品卡片展示“主礼 / 副礼”标签。
- 聊天流式接口支持方案摘要：
  - 可选择直接把角色写进 `product_cards`。
  - 或增加 `plan_summary` 事件。
  - 初版推荐优先使用“写进 product_cards”，改动更小。
- 对比页也能看到主副礼标识，方便继续 A/B 测试算法体验。

不做：

- 不重新设计整个聊天 UI。
- 不做复杂方案对比表。
- 不让前端自己推断主副礼。
- 不让 LLM 修改商品角色；角色来自后端方案裁判。

## 建议数据结构

初版可直接扩展 `ProductCard`：

```py
class ProductCard(BaseModel):
    ...
    gift_role: Literal["main_gift", "addon_gift"] | None = None
```

推荐服务在选中方案后，将 `selected_plan.gift_roles[product_id]` 写入最终 `products`。

前端类型同步：

```ts
export type GiftRole = 'main_gift' | 'addon_gift';

export interface ProductCardData {
  ...
  gift_role?: GiftRole | null;
}
```

## Prompt 方案上下文

建议在 `build_chat_recommendation_prompt` 中新增 `selected_plan` 参数，格式化为：

```text
后端已选择推荐方案：
- 方案类型：budget_optimized
- 裁判理由：组合方案相关度接近默认方案，且预算利用更合理
- 原始预算：500 元
- 预算语义上限：650 元
- 方案总价：477 元
- 主副礼角色：
  - PROD-AROMA-002: main_gift
  - PROD-AROMA-004: addon_gift
```

模型回复要求：

- 先给 1-2 句整体方案解释。
- 再说明主礼和副礼各自承担的作用。
- 商品名称和 product_id 必须来自候选列表。
- 不要输出内部 objective_score、relevance_score 等算法分数。

## 前端展示建议

商品卡片角标：

- `main_gift`：显示“主礼”，颜色偏红或深色。
- `addon_gift`：显示“副礼”，颜色偏紫或灰色。

标题区可保留 `AI 智能推荐`，旁边增加方案类型文本：

```text
AI 智能推荐 · 组合方案
```

如果当前消息里所有商品都没有 `gift_role`，保持现有样式不变。

## 建议文件

```text
backend/app/schemas/product.py
backend/app/schemas/chat.py
backend/app/services/recommendation_service.py
backend/app/services/chat_service.py
backend/app/agent/graph.py
backend/app/agent/prompts_lib/chat_recommendation.py
frontend/src/api/chat.ts
frontend/src/hooks/useGiftChat.ts
frontend/src/pages/AppPages.tsx
docs/specs/recommendation/README.md
```

## 验收标准

- 推荐服务最终返回的 `products` 中包含 `gift_role`。
- 流式聊天返回的 `product_cards` 中包含 `gift_role`。
- AI 回复能自然说明：
  - 主礼是什么。
  - 副礼是什么。
  - 为什么这样搭配。
  - 如有略超原始预算，为什么仍在用户允许范围内。
- 前端商品卡片能展示“主礼 / 副礼”角标。
- `/compare` 对比页能保留主副礼信息，不丢字段。
- 后端编译、服务级样例、API 样例和前端 build 通过。

## 风险点

- Prompt 里注入太多方案字段会让回复变啰嗦，需要限制模型只说用户关心的解释。
- 前端角标不能挤压商品标题，移动端需要保持卡片稳定高度。
- 如果只有一个商品，显示“主礼”可以接受，但不应强行解释副礼。
- 如果方案没有 `gift_roles`，必须兼容旧数据。

## 执行记录

- 状态：已完成
- 规约更新：
  - 确认 R14 不新增复杂 `plan_summary` 流式事件，初版直接把 `gift_role` 写入 `ProductCard`，沿用现有 `product_cards` 事件。
  - 明确直接大模型对比链路不注入候选商品和方案上下文，避免污染 `/compare` 的 A/B 对比。
- 实现内容：
  - 更新 `backend/app/schemas/product.py`：
    - 新增 `GiftRole = Literal["main_gift", "addon_gift"]`。
    - `ProductCard` 新增 `gift_role`。
  - 更新 `backend/app/services/budget_optimizer_service.py`：
    - `RecommendationPlan.products` 中的商品也会写入 `gift_role`。
  - 更新 `backend/app/services/recommendation_service.py`：
    - 最终返回的 `products` 根据选中方案的 `gift_roles` 写入 `gift_role`。
  - 更新 `backend/app/agent/prompts_lib/chat_recommendation.py`：
    - 候选商品白名单中加入角色信息。
    - 新增方案解释指令，要求模型说明主礼、副礼、搭配理由和预算浮动原因。
    - 新增 `selected_plan` prompt 上下文格式化。
  - 更新 `backend/app/agent/graph.py`：
    - `run / astream / _build_prompt` 支持 `selected_plan`。
    - 修复 `candidate_products=None` 被误转成空列表的问题，避免直连大模型链路被注入“无候选商品”指令。
  - 更新 `backend/app/services/chat_service.py`：
    - 构造候选商品 payload 时加入 `gift_role`。
    - 构造选中方案 payload，包含方案类型、裁判理由、总价、原预算、预算上限、超预算比例和主副礼角色。
    - 仅在 `hybrid_algorithm / llm_rerank` 链路注入候选商品与方案上下文。
    - 非流式算法接口也能返回后端推荐商品。
  - 更新 `frontend/src/api/chat.ts`：
    - 新增 `GiftRole` 类型。
    - `ProductCardData` 新增 `gift_role`。
  - 更新 `frontend/src/pages/AppPages.tsx`：
    - 推荐商品卡片显示“主礼 / 副礼”角标。
    - 当消息商品包含角色时，推荐区标题显示 `AI 智能推荐 · 组合方案`。
    - `/compare` 的商品小卡也显示主副礼标识。
- 验证结果：
  - 后端 `python -m compileall app` 通过。
  - 服务级验证：
    - 输入 `给女朋友生日礼物，预算500左右，可以再加一点，想搭配一套`。
    - 最终选择 `budget_optimized`。
    - 返回商品包含：
      - `PROD-AROMA-002 / main_gift / 388`
      - `PROD-AROMA-004 / addon_gift / 89`
  - 流式聊天验证：
    - `product_cards` 事件分别返回 `main_gift` 和 `addon_gift`。
    - 最终返回 `done` 事件。
  - 评测验证：
    - `EvalService().run(strategy="hybrid_algorithm")` 执行 9 条 case，失败 0 条。
    - 可协商预算组合 case 的计划中包含 `gift_roles`。
  - 前端 `npm run build` 通过。
- 当前发现：
  - 主副礼已经贯通到后端接口、流式事件和前端展示。
  - 目前 AI 回复是否稳定提到主副礼仍依赖 prompt 遵循度；如果后续发现模型偶尔忽略，可以增加更硬的回复模板或在后端先生成一段方案摘要。
- 后续建议：
  - R15 可以把 `gift_role_hint / complement_with / category_group` 补进商品知识库，让主副礼角色不只依赖价格和分数推断。
  - 如果要进一步稳定回复，可以新增 `plan_summary` 字段，由后端规则生成一句确定性方案摘要，再交给模型润色。
