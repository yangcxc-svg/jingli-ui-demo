# 任务 R11：约束放宽与候选不足协商策略

## 背景

在 `/compare` 对比测试中，我们观察到：

- 推荐算法能继承会话记忆、过滤用户不喜欢的上一轮商品，并继续给出真实候选商品。
- 直接调用大模型在候选不足时，会主动询问用户是否愿意调整预算、偏好或场景。

这说明当前推荐算法已经具备“稳定选商品”的能力，但还缺少更像真人导购的“协商能力”：当候选不足、候选质量不高或用户连续否定时，不应该只硬推剩余商品，而应该解释约束冲突，并给出可选择的放宽方向。

## 目标

让推荐系统在候选不足或约束过紧时，主动提出可操作的放宽建议，而不是继续硬推荐低质量候选。

理想效果：

```text
当前 500 元预算内，适合“女朋友生日 + 有心意”的候选已经比较少。
你可以选择：
1. 预算放宽到 600-800 元，我可以考虑轻奢香薰/更精致礼盒。
2. 保持 500 元，我继续从实用类、咖啡、运动健康类里找。
3. 告诉我她是否喜欢咖啡、运动、数码或香氛，我再缩小范围。
```

## 范围

需要实现：

- 定义候选不足判断：
  - 返回商品数低于阈值。
  - 候选被画像/不喜欢列表过滤过多。
  - Top N 分数低于阈值。
  - 用户连续表达“不喜欢 / 换一个 / 不合适”。
- 定义约束放宽方向：
  - 放宽预算。
  - 放宽品类或偏好。
  - 放宽场景限制。
  - 询问兴趣偏好。
  - 建议保持预算但切换礼物类型。
- 推荐结果返回协商信息：
  - `needs_relaxation`。
  - `relaxation_reason`。
  - `relaxation_options`。
  - `suggested_questions`。
- 聊天回复中优先表达协商建议，再展示候选商品。
- 评测集中增加候选不足和连续否定 case。

不做：

- 不做复杂多目标优化器。
- 不自动替用户修改预算或偏好。
- 不把放宽建议伪装成已经确认的用户意图。
- 不强制停止推荐；可在给出少量候选的同时提示“可放宽”。

## 建议数据结构

```py
class RelaxationOption(BaseModel):
    option_id: str
    label: str
    description: str
    patch: dict[str, object] = {}


class RecommendationResult(BaseModel):
    ...
    needs_relaxation: bool = False
    relaxation_reason: str | None = None
    relaxation_options: list[RelaxationOption] = []
    suggested_questions: list[str] = []
```

## 候选不足判断建议

初版可以使用简单规则：

```text
needs_relaxation =
  returned_count < requested_max_products
  OR profile_filtered_count >= 2
  OR top_score < 40
  OR user_negative_feedback_count_in_session >= 1
```

注意：

- `returned_count < requested_max_products` 不能单独作为强信号，有些场景本来只需要 1-2 个精品。
- `profile_filtered_count` 是重要信号：说明用户已经否定过一批商品。
- 如果仍然有高质量候选，可以边推荐边给放宽建议。

## 放宽策略建议

### 预算放宽

适用：

- 用户预算较低。
- 当前预算内候选少。
- 预算上浮 20%-50% 后可能有更好选择。

示例：

```text
如果预算可以放宽到 600-800 元，选择会更丰富，尤其是轻奢香薰、精致礼盒和小家电。
```

### 偏好补充

适用：

- 用户只说“不喜欢这些”。
- 系统不知道用户具体不喜欢的是品类、价格、风格还是品牌。

示例：

```text
你更想避开香薰、茶礼，还是觉得这些不够实用？告诉我一个方向，我可以换一类推荐。
```

### 品类切换

适用：

- 同品类候选已被用户否定。
- 剩余候选分数一般。

示例：

```text
如果不考虑香薰和茶礼，可以切到咖啡器具、运动健康、数码小配件这类更实用的礼物。
```

### 场景放宽

适用：

- 场景标签过窄，召回不足。

示例：

```text
如果不局限于生日场景，也可以按“日常关怀”方向挑选，礼物会更实用。
```

## 建议文件

```text
backend/app/schemas/recommendation.py
backend/app/services/constraint_relaxation_service.py
backend/app/services/recommendation_service.py
backend/app/agent/prompts_lib/chat_recommendation.py
backend/app/services/eval_service.py
frontend/src/api/chat.ts
frontend/src/pages/AppPages.tsx
```

## 验收标准

- 当用户第二轮说“不喜欢这些，换一个”时，系统能：
  - 继承上一轮对象、场景和预算。
  - 过滤上一轮商品。
  - 返回新的候选商品。
  - 同时给出至少 2 个可操作的放宽选项。
- 当预算明显限制候选时，系统能建议用户是否愿意放宽预算。
- 当用户未表达具体偏好时，系统能追问偏好方向，而不是只继续硬推商品。
- 前端能展示放宽建议，至少以文本或 chip 的形式展示。
- R10 评测集中能看到候选不足 case 的 `needs_relaxation` 命中情况。

## 风险点

- 不能过度劝用户加预算，语气要克制。
- 放宽建议不能替用户做决定，只能作为选项。
- 如果候选商品质量已经足够，不要频繁弹出放宽建议。
- 放宽策略要和用户明确禁忌兼容，不能建议用户重新考虑已明确不要的品类。

## 执行记录

- 状态：已完成
- 规约更新：
  - 确认 R11 不做成 skill，而是作为推荐管线中的约束协商策略模块实现。
  - 明确候选不足、画像过滤过多、低分候选、用户负反馈都会触发放宽建议。
  - 明确放宽建议只作为选项，不自动替用户修改预算或偏好。
- 实现内容：
  - 更新 `backend/app/schemas/recommendation.py`：
    - 新增 `RelaxationOption`。
    - `RecommendationResult` 新增 `needs_relaxation / relaxation_reason / relaxation_options / suggested_questions`。
  - 新增 `backend/app/services/constraint_relaxation_service.py`：
    - 根据返回数量、候选数量、画像过滤数量、用户负反馈、Top 分数判断是否需要放宽。
    - 生成预算放宽、品类切换、说明不喜欢原因、放宽场景限制等选项。
    - 生成可追问问题。
  - 更新 `backend/app/services/recommendation_service.py`：
    - 在推荐排序和画像过滤之后调用 `ConstraintRelaxationService`。
    - 将放宽判断写入响应和 pipeline。
  - 更新 `backend/app/agent/prompts_lib/chat_recommendation.py`：
    - 增加约束偏紧时的协商式回复指令。
    - 将放宽原因、选项和追问方向注入聊天 prompt。
  - 更新 `backend/app/agent/graph.py` 与 `backend/app/services/chat_service.py`：
    - 支持向模型传入 `relaxation` 上下文。
    - 流式接口新增 `relaxation_options` 事件。
  - 更新 `backend/app/schemas/chat.py`：
    - `ChatResponse` 与 `StreamEvent` 增加放宽建议字段。
  - 更新 `backend/app/services/eval_service.py`：
    - 增加低预算候选不足 case。
    - case 快照返回 `needs_relaxation / relaxation_options / suggested_questions`。
    - 聚合指标增加 `relaxation_accuracy / relaxation_rate`。
  - 更新前端：
    - `frontend/src/api/chat.ts` 增加放宽建议类型和流式事件类型。
    - `frontend/src/hooks/useGiftChat.ts` 接收并保存放宽建议事件。
    - `frontend/src/pages/AppPages.tsx` 在聊天和对比页展示“可以这样调整”的 chips。
- 验证结果：
  - 后端 `python -m compileall app` 通过。
  - 服务级验证：
    - 第一轮 `送女朋友生日礼物，预算500元，要有心意` 正常返回商品，`needs_relaxation=False`。
    - 第二轮同会话 `不喜欢这些，换一个` 继承上一轮对象/场景/预算，过滤上一轮商品，返回新商品。
    - 第二轮 `needs_relaxation=True`。
    - 第二轮返回 4 个放宽选项：
      - `raise_budget`
      - `switch_category`
      - `clarify_dislike`
      - `relax_scene`
  - 流式聊天验证：
    - 第二轮先返回 `relaxation_options` 事件。
    - 随后返回文本和商品卡片。
  - API 验证：
    - `POST /api/products/recommendations` 第二轮返回 `needs_relaxation=True` 和不少于 2 个 `relaxation_options`。
    - `POST /api/eval/run?strategy=hybrid_algorithm` 返回 200，执行 7 条 case。
    - 评测指标包含 `relaxation_accuracy` 与 `relaxation_rate`。
  - 前端 `npm run build` 通过。
- 当前发现：
  - R11 已能把“大模型直出中比较好的协商能力”吸收到算法流程里。
  - 初版触发条件偏保守/规则化，后续可结合 R10 评测继续调阈值，避免过度建议放宽。
- 后续建议：
  - 让前端 chips 可点击，点击后把对应 `patch` 转成下一轮推荐请求。
  - 在 R10 评测里区分“应该放宽”和“不应该放宽”的 case，继续校准 `relaxation_accuracy`。
  - 后续可以把候选不足原因拆成更细的枚举，方便前端展示不同样式。
