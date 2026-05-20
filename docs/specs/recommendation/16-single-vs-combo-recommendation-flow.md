# 任务 R16：单品 Top3 与组合方案双流程

## 背景

R15 已经引入礼物形态判断：系统能根据用户意图判断更适合 `single_gift`、`gift_combo` 或 `either`，并提供完整送礼方案字段。

但当前实现仍有两个明显断点：

- 单品路径过于“Top1 化”，用户如果只是想挑一个礼物，应该看到最合适的 3 个单品并能比较。
- v2 前端推荐链路仍主要调用 `/gift-plan/generate`，没有真正消费 R15 的 `/gift-solution/generate` 与 `shape_decision`。

因此 R16 要把推荐产品形态明确拆成两条可见流程：

```text
用户只需要一个礼品 -> 单品推荐 Top3 + 每个商品推荐理由
用户需要一套礼品组合 -> 最优商品组合 + 完整送礼解决方案
```

## 目标

1. 后端形态判断命中 `single_gift` 时，推荐 3 个候选单品，而不是只返回 1 个。
2. 后端形态判断命中 `gift_combo` 时，优先返回被方案裁判选中的最优组合。
3. v2 前端画像表单调用 `/gift-solution/generate`，使推荐页能根据 `shape_decision` 区分展示。
4. 单品模式展示“AI 精选 3 个单品”。
5. 组合模式展示“AI 定制 1 套组合方案”和送礼话术、时机、地点、包装、避坑建议。

## 非目标

- 不做真实图片生成。
- 不做真实语音卡生成。
- 不新增数据库订单或持久化用户画像。
- 不改旧版 `/jingli` 聊天链路。

## 业务规则

### 单品模式

触发条件：

- 用户说“一个礼物 / 一件 / 单品 / 简单点 / 不要复杂”。
- 或者场景较轻、预算较低、没有明显组合诉求。

返回要求：

- `shape_decision.shape = single_gift`
- `shape_decision.recommended_product_count = 3`
- `products` 返回最多 3 个商品。
- 第一项为首推，其余为备选。
- 商品 `gift_role` 可标记为 `main_gift` / `alternative_gift`。

### 组合模式

触发条件：

- 用户说“组合 / 礼单 / 搭配 / 一套 / 多个”。
- 或者正式场景、高预算、多目标诉求。

返回要求：

- `shape_decision.shape = gift_combo`
- `products` 返回一个最优组合内的商品。
- 组合商品保留 `main_gift / addon_gift`。
- 响应包含完整送礼解决方案字段。

## 接口行为

v2 前端应调用：

```http
POST /api/gift-solution/generate
```

请求仍可先由前端拼接 `message`，但必须包含画像表单中的关系、年龄、预算、标签等信息。

响应由前端映射为：

- `shapeDecision`
- `solution`
- `recommendations`

## 验收标准

- 输入“想给朋友生日送一个礼物，预算500，简单点”：
  - 返回/展示单品模式。
  - 推荐页展示 3 个候选单品。
  - 不展示主副礼组合方案文案。

- 输入“第一次见家长，预算3000，想准备一套体面点的礼物”：
  - 返回/展示组合模式。
  - 推荐页展示一个组合方案。
  - 展示送礼话术、时机、地点、包装建议和避坑提醒。

- v2 表单点击“立即定制 AI 专属好物”后，调用 `/gift-solution/generate`。
- 前端 `npm run build` 通过。
- 后端至少能通过轻量脚本验证 `GiftShapeService` 的单品/组合数量决策。

## 实施记录

- 状态：已完成
- 执行日期：2026-05-20
- 修改文件：
  - `backend/app/services/gift_shape_service.py`
  - `backend/app/services/gift_solution_service.py`
  - `frontend/src/v2/api/v2Api.ts`
  - `frontend/src/v2/pages/V2RecommendationsPage.tsx`
  - `docs/specs/recommendation/README.md`
  - `docs/specs/recommendation/16-single-vs-combo-recommendation-flow.md`
- 实现结果：
  - 单品形态判断现在返回 `recommended_product_count=3`，用于 Top3 单品推荐。
  - 单品方案保留最多 3 个商品，首个商品标记为 `main_gift`，其余作为备选候选展示。
  - 组合方案继续走组合优化与方案裁判，前端展示完整送礼解决方案。
  - v2 画像表单推荐链路已切换为 `/gift-solution/generate`。
  - v2 推荐页根据 `shape_decision.shape` 展示单品模式或组合模式。
- 验证结果：
  - `npm run build` 通过。
  - 后端轻量脚本验证通过：
    - “想给朋友生日送一个礼物，预算500，简单点” -> `single_gift`，`recommended_product_count=3`。
    - “第一次见家长，预算3000，想准备一套体面点的礼物” -> `gift_combo`，`use_combo_optimizer=True`。
