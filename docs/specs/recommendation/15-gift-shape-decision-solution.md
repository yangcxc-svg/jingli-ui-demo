# 任务 R15：礼物形态决策与完整送礼方案

## 背景

R12-R14 已经把“推荐商品”推进到了“推荐方案”：

- 后端能生成 `ranked_topn / budget_optimized`。
- 方案裁判能选择最终方案。
- 商品卡片能展示 `main_gift / addon_gift`。
- AI 回复可以解释主礼、副礼和预算浮动。

但真实送礼场景里，用户的痛点并不只是“买什么”：

- 这个场景适合送单一礼品，还是组合礼品？
- 如果适合单一礼品，是否应该避免过度组合，保持体面、克制、清晰？
- 如果适合组合礼品，如何组合成“主礼 + 副礼”？
- 送礼时怎么说？
- 什么时候送、在哪里送更自然？
- 要不要提前包装、附卡片、避开哪些表达？
- 如果对方推辞，怎么回应？

因此 R15 要把推荐系统从“商品推荐 Agent”进一步升级为“送礼解决方案 Agent”：先判断送礼形态，再调用合适推荐路径，最后生成完整的送礼行动建议。

## 目标

新增一个上层决策能力：根据用户送礼意图和场景，判断本次更适合“单一礼品”还是“组合礼品”，并生成完整送礼方案。

理想流程：

```text
用户：第一次见家长，预算3000，想体面点但别太贵

1. 礼物形态决策：
   - 场景正式、关系敏感、需要体面表达
   - 推荐组合礼品：主礼 + 副礼

2. 商品推荐：
   - 组合礼品：走 R12-R14 组合优化与主副礼方案
   - 单一礼品：走更克制的 Top1/TopN 单品推荐，不强行组合

3. 完整送礼方案：
   - 推荐商品/组合
   - 推荐理由
   - 送礼话术
   - 什么时候送
   - 在哪里送
   - 包装与卡片建议
   - 对方推辞时怎么回应
   - 避坑提醒
```

## 核心原则

- 不是所有场景都应该组合礼品。
- 单一礼品和组合礼品应由用户意图、关系、场景、预算和偏好共同决定。
- 组合推荐才需要重点使用预算优化和主副礼建模。
- 单一礼品可以使用现有推荐算法，但应偏向“选一个最合适的主礼”，不要为了组合而组合。
- 最终大模型负责表达完整方案，但商品选择必须来自后端可控候选。

## 形态定义

### single_gift

适合：

- 用户明确说“一个礼物 / 一件 / 单品 / 不要太复杂”。
- 场景轻量，如朋友生日、同事小礼物、日常关怀。
- 预算较低，组合容易显得凑数。
- 商品本身已经足够完整，比如高品质香薰、智能手表、咖啡机。

推荐策略：

- 返回 1 个主礼，最多给 1-2 个备选。
- 商品卡片可标记为 `main_gift`。
- 回复重点解释“为什么这个单品足够合适”。
- 不强行输出副礼。

### gift_combo

适合：

- 用户明确说“组合 / 礼单 / 搭配 / 一套 / 多个”。
- 场景正式或高压，如见家长、婚礼/订婚、送领导/客户、探望长辈。
- 预算中高，组合能提升体面感和完整度。
- 用户希望兼顾多个目标，如体面 + 实用、健康 + 心意。

推荐策略：

- 调用 R12-R14 的组合优化方案。
- 返回主礼 + 副礼。
- 解释搭配逻辑和预算使用。

### either

适合：

- 用户信息不足，单品和组合都合理。
- 可先给一个默认判断，并附带“也可以换成组合/单品”的选择。

推荐策略：

- 若预算低，默认 single_gift。
- 若预算中高且场景正式，默认 gift_combo。
- 前端可后续做“切换成组合 / 切换成单品”按钮。

## 建议数据结构

```py
GiftShape = Literal["single_gift", "gift_combo", "either"]


class GiftShapeDecision(BaseModel):
    shape: GiftShape
    confidence: float = 0.0
    reason: str
    signals: list[str] = []
    recommended_product_count: int = 1
    use_combo_optimizer: bool = False
```

完整送礼方案：

```py
class GiftSolution(BaseModel):
    solution_id: str
    shape: GiftShape
    title: str
    summary: str
    products: list[ProductCard]
    total_amount: Decimal | None = None
    recommendation_reason: str
    giving_timing: str
    giving_place: str
    gift_talk: str
    recipient_reaction_reply: str
    packaging_advice: str
    avoid_tips: list[str] = []
    follow_up_question: str | None = None
```

## 形态判断建议

初版采用“规则优先 + LLM 辅助”的方式。

### 规则信号

强制组合：

- 用户说：组合、礼单、搭配、一套、多个、几件。

倾向组合：

- 场景：见家长、婚礼/订婚、探望长辈、送领导/客户、节日送礼。
- 预算档：mid/high/luxury。
- 风格：体面、高端、正式、稳重、健康关怀。
- 用户表达多个目标：既要体面又要实用、健康一点但别太贵。

强制单品：

- 用户说：一个、一件、单品、不要复杂、简单点。

倾向单品：

- 预算 low。
- 关系轻量：朋友、同事、学生党。
- 场景轻量：普通生日、日常关怀。

### LLM 辅助

当规则冲突或信息不足时，让 LLM 输出结构化判断：

```json
{
  "shape": "single_gift|gift_combo|either",
  "confidence": 0.82,
  "reason": "第一次见家长属于正式场景，组合礼品更能体现体面和完整度",
  "signals": ["正式场景", "预算中高", "体面诉求"],
  "recommended_product_count": 2
}
```

注意：

- LLM 只判断形态，不直接编造商品。
- 形态判断结果要写入 pipeline，便于评测。

## 推荐路径

### single_gift 路径

推荐请求：

```py
RecommendationRequest(
  max_products=1,
  strategy="hybrid_algorithm",
  allow_generic_recommendation=False
)
```

后处理：

- 若返回多个候选，只取最优主礼作为主推荐。
- 可保留 1-2 个备选，但前端主展示单品。
- `gift_role=main_gift`。

### gift_combo 路径

推荐请求：

```py
RecommendationRequest(
  max_products=3,
  strategy="hybrid_algorithm",
  include_fallback=True
)
```

后处理：

- 使用 R12-R14 的 `budget_optimized` / `ranked_topn` 方案。
- 保留 `main_gift / addon_gift`。
- 如果组合候选不足，回退到 single_gift 并说明原因。

## 完整送礼方案生成

大模型输入：

- 用户原始需求。
- 结构化意图。
- 形态判断结果。
- 最终商品白名单。
- 选中方案信息。
- 预算语义。

大模型输出必须包含：

- 推荐总结。
- 商品/组合推荐理由。
- 送礼话术。
- 送礼时机。
- 送礼地点。
- 包装或卡片建议。
- 对方推辞时的回应。
- 避坑提醒。

示例：

```text
送礼话术：
“叔叔阿姨，第一次上门也不知道您二位平时喜欢什么，就准备了一点日常能用得上的心意，希望别嫌弃。”

什么时候送：
建议进门寒暄后、落座前递出，不要等饭桌上再拿出来，避免显得太正式或让对方有压力。

在哪里送：
在玄关或客厅递给对方更自然；如果东西较多，可以由伴侣帮忙一起递。
```

## 建议文件

```text
backend/app/schemas/gift_solution.py
backend/app/services/gift_shape_service.py
backend/app/services/gift_solution_service.py
backend/app/agent/prompts_lib/gift_solution.py
backend/app/api/routes/gift_solution.py
backend/app/api/router.py
frontend/src/api/giftSolution.ts
frontend/src/pages/AppPages.tsx
docs/specs/recommendation/README.md
```

可选复用：

```text
backend/app/services/gift_plan_service.py
backend/app/schemas/gift_plan.py
backend/app/agent/prompts_lib/gift_plan.py
```

## 验收标准

- 输入“一个简单点的生日礼物，预算300”时，形态判断为 `single_gift`。
- 输入“第一次见家长，预算3000，体面点”时，形态判断为 `gift_combo`。
- 输入“预算500左右，可以再加一点，想搭配一套”时，形态判断为 `gift_combo`。
- 单品路径不强行返回副礼。
- 组合路径返回主礼和副礼。
- 完整送礼方案包含：
  - 送礼话术。
  - 送礼时机。
  - 送礼地点。
  - 包装建议。
  - 对方推辞回应。
  - 避坑提醒。
- 商品仍然来自后端候选白名单。
- 后端编译、服务级样例、API 样例和前端 build 通过。

## 风险点

- 如果把所有正式场景都判断为组合，可能显得过度设计，需要保留预算和用户偏好的约束。
- 完整送礼方案容易变长，前端展示需要分块，否则聊天体验会臃肿。
- LLM 生成话术时不能过度油腻或冒犯，尤其是见家长、领导、客户场景。
- 单品路径和组合路径要保持可评测，不能只靠自然语言判断。

## 分阶段实现建议

### R15.1 后端形态决策

- 新增 `GiftShapeDecision`。
- 新增 `GiftShapeService`。
- 推荐管线根据 shape 调整 `max_products` 和组合优化使用方式。

### R15.2 完整送礼方案生成

- 新增 `GiftSolutionService`。
- 新增结构化 prompt 和响应 schema。
- 支持单品/组合两种方案说明。

### R15.3 前端展示

- 在聊天回复中展示方案块：
  - 推荐总结。
  - 商品卡片。
  - 送礼话术。
  - 时机/地点。
  - 避坑提醒。

### R15.4 评测

- 增加形态判断 golden cases。
- 增加完整方案字段完整性检查。
- 观察单品/组合误判率。

## 执行记录

- 状态：已完成
- 规约更新：
  - 确认 R15 是“送礼解决方案”上层编排，不替代 R12-R14 的商品推荐和组合优化。
  - 初版采用规则优先的 `GiftShapeService` 判断 `single_gift / gift_combo / either`，LLM 负责最终自然语言方案生成。
  - 前端先接入一个独立 `/gift-solution` 页面，避免影响现有聊天主流程。
- 实现内容：
  - 新增 `backend/app/schemas/gift_solution.py`：
    - `GiftShapeDecision`
    - `GiftSolutionGenerateRequest`
    - `GiftSolutionResponse`
  - 新增 `backend/app/services/gift_shape_service.py`：
    - 根据用户关键词、场景、预算、风格信号判断礼物形态。
    - 支持强制单品、强制组合、正式场景倾向组合、低预算倾向单品等规则。
  - 新增 `backend/app/agent/prompts_lib/gift_solution.py`：
    - 定义完整送礼方案 JSON schema。
    - 要求输出推荐总结、推荐理由、送礼话术、送礼时机、送礼地点、包装建议、推辞回应、避坑提醒。
    - 商品只能来自候选白名单。
  - 新增 `backend/app/services/gift_solution_service.py`：
    - 抽取用户意图。
    - 调用 `GiftShapeService` 判断单品/组合。
    - 根据形态调整推荐路径：
      - `single_gift`: `max_products=1`。
      - `gift_combo`: `max_products=3` 并启用组合候选。
    - 调用推荐服务拿真实商品。
    - 调用大模型生成完整送礼方案。
    - LLM 解析失败时提供确定性兜底方案。
  - 新增 `backend/app/api/routes/gift_solution.py`：
    - `POST /api/gift-solution/generate`。
  - 更新 `backend/app/api/router.py`：
    - 注册 `gift-solution` 路由。
  - 新增 `frontend/src/api/giftSolution.ts`：
    - 前端请求和响应类型。
  - 更新 `frontend/src/pages/AppPages.tsx`：
    - 新增 `GiftSolutionPage`。
    - 支持输入送礼需求、生成完整方案、展示形态判断、商品卡片、推荐理由、话术、时机、地点、包装建议、推辞回应和避坑提醒。
    - 京礼首页增加“完整送礼方案”入口。
  - 更新 `frontend/src/App.tsx`：
    - 新增 `/gift-solution` 路由。
- 验证结果：
  - 形态判断服务级验证：
    - `一个简单点的生日礼物，预算300` => `single_gift`。
    - `第一次见家长，预算3000，体面点` => `gift_combo`。
    - `预算500左右，可以再加一点，想搭配一套` => `gift_combo`。
  - 完整方案服务级验证：
    - 单品 case 返回 1 个 `main_gift`。
    - 见家长 case 返回 `main_gift + addon_gift` 组合。
    - 搭配一套 case 返回 `main_gift + addon_gift` 组合。
  - API 验证：
    - `POST /api/gift-solution/generate` 三个验收样例均返回 200。
    - 响应包含：
      - `shape_decision`
      - `products`
      - `gift_talk`
      - `giving_timing`
      - `giving_place`
      - `packaging_advice`
      - `recipient_reaction_reply`
      - `avoid_tips`
  - 编译与构建：
    - 后端 `python -m compileall app` 通过。
    - 前端 `npm run build` 通过。
- 当前发现：
  - R15 已经能把“买什么”扩展为“怎么送”。
  - 当前完整方案页面是独立入口，还没有并入主聊天流。
  - 形态判断初版是规则优先，后续可以在规则冲突时加入 LLM 结构化辅助判断。
- 后续建议：
  - R16 可以把完整方案能力接入主聊天：当用户需求明显是高压送礼场景时，聊天流直接给出方案块。
  - 增加形态判断评测集，统计 `single_gift / gift_combo` 误判率。
  - 前端可以把送礼话术、时机、地点做成可复制卡片。
