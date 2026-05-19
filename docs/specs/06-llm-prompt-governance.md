# 任务 6：大模型调用与 Prompt 治理

## 目标

让大模型输出稳定、可控、可排查，减少“文本推荐和商品卡片不一致”的问题。

## 当前问题

- Prompt 仅有 `backend/app/agent/prompts.py` 中的 `GUIDE_SYSTEM_PROMPT` 一份，未按聊天推荐 / 组合礼单 / 商品重排序等场景拆分，规则容易互相干扰。
- 输出主要靠自然语言，结构化约束不足。`chat_service._split_answer_by_products` 只能用商品名 alias 推断"文本提到了哪个商品"，对应关系不稳定。
- Mock 模式与真实模型模式容易混淆：当 `.env` 配置缺失或写错时，前端只会看到 `Mock LLM response.`，后端没有结构化的状态暴露。
- `LLMClient` 已经能返回 `latency_ms`、`input_tokens`、`output_tokens`，但缺乏统一的"模型调用日志"汇总和查询入口。

## 范围

需要实现：

- 按场景拆分 prompt，将 `prompts.py` 升级为 `prompts` 子包，集中托管所有 prompt 文案与版本号。
- 让组合礼单（非流式）接口获取结构化输出（`selected_product_ids` 等），失败时回退到原有自然语言策略。
- 增加内存版"模型调用日志"，记录 provider / model / prompt_name / prompt_version / latency / input_tokens / output_tokens / 错误信息，并暴露查询接口供观测。
- 健康检查输出当前 LLM 状态（provider / model / is_mock / base_url 是否配置），README 明确真实模型配置和 mock 模式差异。

不做：

- 不暴露 API Key。
- 不在前端直接调用模型。
- 不强制流式聊天返回 JSON（会破坏增量文本体验）；保留 alias 兜底。
- 不接入数据库版的 `ModelCallLog` 表（避免提前耦合部署任务 8）。

## 建议 Prompt 结构

将单文件 `backend/app/agent/prompts.py` 升级为子包：

```text
backend/app/agent/prompts/
  __init__.py          # 对外导出常用 prompt 常量与版本号
  guide_system.py      # 通用导购 system prompt（沿用现有 GUIDE_SYSTEM_PROMPT）
  chat_recommendation.py  # 聊天推荐用户态 prompt 模板与拼接函数
  gift_plan.py         # 组合礼单结构化输出 prompt + JSON schema 说明
  product_rerank.py    # 预留：商品排序 prompt（轮不强制启用）
```

`__init__.py` 必须保留对 `GUIDE_SYSTEM_PROMPT` 等常量的 re-export，避免破坏现有 `from app.agent.prompts import GUIDE_SYSTEM_PROMPT` 调用方。

## 建议结构化输出（仅用于 gift_plan/generate）

```json
{
  "answer": "展示给用户的推荐说明",
  "selected_product_ids": ["PROD-EARBUDS-001"],
  "budget_reason": "预算说明",
  "relationship_tone": "关系分寸说明",
  "follow_up_question": "可选追问"
}
```

解析规则：

- 收到 LLM 文本后，优先用宽松 JSON 抽取（容忍 ```json ... ``` 包裹、前后多余文本）。
- 解析成功时：用 `selected_product_ids` 重排 / 过滤 `RecommendationService` 返回的商品；`answer` 优先于纯文本回复。
- 解析失败或字段缺失：保留 LLM 原文当作 `answer`，商品仍按 `RecommendationService` 结果，不阻塞接口。
- `chat/stream` 流式接口不要求 JSON 输出，但模型若在自然语言中提到商品名，仍由 `chat_service._split_answer_by_products` 做 alias 兜底匹配。

## 模型调用日志

新增 `backend/app/services/model_log_service.py`（内存版单例），在 `LLMClient.generate / astream` 完成后统一写入：

- `trace_id`（从 `app.core.tracing` 中取，没有则随机生成）
- `provider`、`model`
- `prompt_name`、`prompt_version`
- `input_tokens`、`output_tokens`、`latency_ms`
- `success` / `error`
- `created_at`

并暴露：

- `GET /api/eval/model-logs?limit=20`：按时间倒序列出最近调用，便于调试 / 观测。
- 不持久化、不写库，保留 `app/models/model_log.py` 为后续接入的占位。

## 健康检查与 README

- `/api/health/ready` 增加 `llm` 字段：`{ provider, model, is_mock, base_url_configured }`，让前端 / 部署侧不必看日志就能确认配置是否生效。
- README 在「配置」段落补充：mock 与真实模型的差异、如何确认是否 mock、配置错误时的诊断顺序。

## 验收标准

- 模型文本中提到的商品尽量能对应到商品卡片：组合礼单结构化输出可用时由 `selected_product_ids` 决定，聊天流式由 alias 兜底。
- 预算不明确时，模型仍按现有 prompt 引导追问或给分档建议；本轮不强制改 prompt 规则。
- 真实模型配置缺失时，`/api/health/ready` 返回 `is_mock=true`，日志可见 provider/model；前端提示沿用现有 README 指引。
- 敏感配置不会进入 git（现状已达成，`.env` 已 ignore）。
- `prompts` 升级为子包后，现有 `from app.agent.prompts import GUIDE_SYSTEM_PROMPT` 等导入不被破坏。
- `GET /api/eval/model-logs` 返回结构化条目，包含 provider/model/latency/tokens。
- `gift_plan/generate` 在 LLM 返回非 JSON 时仍能返回合理响应（fallback）。

## 风险点

- 模型不一定严格遵守 JSON：必须有解析失败兜底，且不能因为解析失败让接口报 5xx。
- Prompt 不能过度复杂，否则响应变慢：本轮在系统 prompt 基础上加约束，但不要堆叠过多 few-shot。
- 内存版调用日志不能阻塞主流程：写入失败仅记录 warn，不抛异常。
- `prompts` 子包要保持向后兼容，老 import 路径必须保留 re-export。

## 本轮执行记录

已完成：

- Prompt 按场景拆分：新增 `backend/app/agent/prompts_lib/` 子包（`guide_system.py / chat_recommendation.py / gift_plan.py / product_rerank.py`），将原 `prompts.py` 升级为 facade，只做 re-export，保留 `GUIDE_SYSTEM_PROMPT` 等向后兼容 import。
- 新增 prompt 版本号：`GIFT_PLAN_PROMPT_VERSION=gift-plan-v1`、`CHAT_RECOMMENDATION_PROMPT_VERSION=chat-recommendation-v1`，老的 `INTENT_PROMPT_VERSION / RAG_PROMPT_VERSION / RECOMMENDATION_PROMPT_VERSION` 全部保留。
- 组合礼单结构化输出：`build_gift_plan_prompt` 要求模型按固定 JSON schema 输出；`GiftPlanService._parse_structured` 实现宽松 JSON 解析（容忍 ```json``` 围栏、前后多余文本），失败时回落自然语言；`_reorder_products` 按 `selected_product_ids` 重排候选商品，幻觉 id 被过滤，模型未列出的候选保留在末尾。
- 内存版模型调用日志：新增 `backend/app/services/model_log_service.py`（单例 `deque(maxlen=200)`），记录 `trace_id / provider / model / prompt_name / prompt_version / input_tokens / output_tokens / latency_ms / status / error / is_mock / is_stream / created_at`。
- `LLMClient.generate / astream` 接入 `model_log_service.record`，新增 `prompt_name / prompt_version / trace_id` 参数；新增 `is_mock` 属性与 `status()` 方法（不暴露 API Key）。
- `GuideAgent` 调 `LLMClient` 时显式传入 `prompt_name=chat_recommendation`、`prompt_version=CHAT_RECOMMENDATION_PROMPT_VERSION`，便于日志区分聊天 vs 组合礼单。
- 新增 `GET /api/eval/model-logs?limit=20` 接口与 `ModelLogListResponse` schema。
- `/api/health/ready` 输出 `dependencies.llm = { provider, model, is_mock, base_url_configured, api_key_configured }`；`HealthResponse.dependencies` 类型从 `dict[str, str]` 放宽为 `dict[str, Any]` 以承载嵌套对象。
- README 增加「如何确认 LLM 是否走真实模型」段落，列出 5 步诊断顺序，并指向 `/api/eval/model-logs` 排查入口。

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

使用 FastAPI `TestClient` + 当前 `.env`（zhipu / glm-4-flash-250414）验证：

- 向后兼容 import：`from app.agent.prompts import GUIDE_SYSTEM_PROMPT` 等老调用方仍工作。
- `_parse_structured` 三类输入：纯 JSON / ```json``` 围栏 / 前后带噪声文本均解析正确；`'not json'` 与空串返回 `None`。
- `_reorder_products(['C','A','GHOST'])` 对 `[A, B, C]` 返回 `[C, A, B]`，幻觉 `GHOST` 被丢弃。
- `GET /api/health/ready`返回 `dependencies.llm = {'provider':'zhipu','model':'glm-4-flash-250414','is_mock':False,'base_url_configured':True,'api_key_configured':True}`。
- `POST /api/gift-plan/generate` 在真实模型下 5.7s 内返回，结构化解析成功，商品按模型 `selected_product_ids` 重排为 `[PROD-PHONE-001, PROD-BAND-001]`。
- `GET /api/eval/model-logs?limit=5` 返回 1 条日志：`provider=zhipu / model=glm-4-flash-250414 / prompt_name=gift_plan / prompt_version=gift-plan-v1 / input_tokens=507 / output_tokens=135 / latency_ms=5740 / status=success / is_mock=False`。

```bash
cd frontend
npm run build
```

通过（`tsc --noEmit` + `vite build` 均成功，前端契约未受影响）。

验收对照（任务 6 验收标准）：

- ✅ 模型文本中提到的商品对应到商品卡片：组合礼单走 `selected_product_ids` 重排，聊天流式仍由 `chat_service._split_answer_by_products` alias 兜底
- ✅ 真实模型配置缺失时 `/api/health/ready` 会返回 `is_mock=true`，README 已写明排查顺序
- ✅ 敏感配置不会进入 git（现状已达成）
- ✅ `prompts` 升级为子包后老 import 路径保留 re-export
- ✅ `GET /api/eval/model-logs` 返回结构化条目，含 provider/model/latency/tokens
- ✅ `gift_plan/generate` 在 LLM 非 JSON 输出时仍回落到自然语言 `answer`

后续可继续做：

- 把 `selected_product_ids` 思路也用到聊天流式（先收完文本，再做尾部 JSON 抽取），替换 alias 兜底。
- 接入 `app/models/model_log.py` 表，做持久化版调用日志（与任务 8 部署一起推进）。
- 实际落地 `PRODUCT_RERANK_PROMPT`，在 `RecommendationService` 中加一层 LLM 轻量重排。
- 给 `_parse_structured` 与 `_reorder_products` 写正式 pytest 用例（任务 7）。