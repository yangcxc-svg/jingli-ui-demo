# 任务 R1：送礼意图结构化抽取

## 目标

把用户自然语言请求解析成稳定的 `GiftIntent`，作为后续召回、打分、排序和追问的统一输入。

## 背景

当前推荐主要依赖用户原始文本检索知识库。这样容易出现两个问题：

- 用户说法变化会直接影响召回结果。
- 后端算法不知道用户到底在送谁、什么场景、多少预算、有什么禁忌。

## 范围

需要实现：

- 新增 `GiftIntent` schema。
- 新增 `IntentExtractor` 服务。
- LLM 负责从用户输入中抽取结构化意图。
- 当 LLM 失败时，提供规则兜底解析预算、场景、人群。
- 将 `GiftIntent` 接入 `RecommendationService`，作为推荐请求的结构化补充输入。

不做：

- 不在本任务里改排序算法。
- 不要求一次性支持所有复杂场景。

## 建议数据结构

```py
class GiftIntent(BaseModel):
    recipient: str | None = None
    relationship: str | None = None
    scenario: str | None = None
    budget: Decimal | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    preferences: list[str] = []
    avoid: list[str] = []
    gift_style: list[str] = []
    must_ask: bool = False
    missing_slots: list[str] = []
```

## 建议文件

```text
backend/app/schemas/gift_intent.py
backend/app/services/intent_extractor.py
backend/app/agent/prompts_lib/intent_extraction.py
```

## 本轮实施边界

当前项目已经有：

- `backend/app/agent/prompts_lib/`：场景化 prompt 目录。
- `backend/app/services/recommendation_service.py`：统一商品推荐服务。
- `RecommendationRequest` 已支持 `scenarios / target_people / budget_level`。

因此本轮实现：

- 新增 `GiftIntent` 与 `IntentExtractor`。
- `IntentExtractor` 优先调用 LLM 抽取 JSON，失败或 mock 时使用规则兜底。
- `RecommendationService.recommend_products` 在缺少显式过滤字段时，自动调用 `IntentExtractor` 补齐 `budget / scenarios / target_people / preference`。
- 不改变现有前端接口协议，不新增 API 路由。

## 验收标准

- “想给25岁女生送生日礼物，预算500元”能抽取出女生、生日、500 元。
- “见家长，预算3000，体面点”能抽取出见家长、长辈/对象父母、3000、体面。
- 缺少预算时 `missing_slots` 包含 `budget`。
- LLM 返回非法 JSON 时，系统不会崩溃，能用规则兜底。

## 风险点

- 不要让 LLM 自己创造不存在的商品 ID。
- 抽取结果需要可调试，建议记录原始输入和解析结果。

## 本轮执行记录

已完成：

- 新增 `backend/app/schemas/gift_intent.py`：
  - 定义 `GiftIntent`
  - 支持 `recipient / relationship / scenario / budget / preferences / avoid / gift_style / target_people / scenarios / budget_level / missing_slots`
  - 根据预算自动推导 `budget_level`
  - 自动补齐 `missing_slots`
- 新增 `backend/app/agent/prompts_lib/intent_extraction.py`：
  - 定义意图抽取 system prompt
  - 定义 JSON schema 提示
  - 定义 `build_intent_extraction_prompt`
- 更新 `backend/app/agent/prompts.py`：
  - 注册 `INTENT_EXTRACTION_PROMPT_VERSION`
  - re-export 意图抽取 prompt 构建函数
- 新增 `backend/app/services/intent_extractor.py`：
  - 优先使用 LLM 抽取 JSON
  - LLM mock、非法 JSON、校验失败时自动降级到规则兜底
  - 规则兜底支持预算、常见送礼场景、送礼对象、人群、关系、风格、禁忌抽取
- 更新 `backend/app/schemas/recommendation.py`：
  - `RecommendationRequest` 支持 `gift_intent`
  - `RecommendationResult` 返回 `GiftIntent`
- 更新 `backend/app/services/recommendation_service.py`：
  - `recommend_products` 会先解析 `GiftIntent`
  - 用 `GiftIntent` 补齐 `budget / scenarios / target_people / preference / budget_level`
  - 增加逐级放宽召回策略，避免商品数据场景标签不足时推荐结果为空

验证结果：

```bash
cd backend
python -m compileall app
```

通过。

规则兜底抽取验证：

```text
输入：想给25岁女生送生日礼物，预算500元。
输出：scenario=生日, recipient=女生, budget=500, missing_slots=[]

输入：见家长，预算3000，体面点
输出：scenario=见家长, recipient=对象父母, budget=3000, gift_style=['体面'], missing_slots=[]

输入：推荐个礼物
输出：missing_slots=['recipient', 'scenario', 'budget'], must_ask=True

输入：送领导，不想太冒犯
输出：scenario=送领导/客户, recipient=领导, avoid=['太冒犯'], missing_slots=['budget']
```

推荐服务接入验证：

```text
输入：想给25岁女生送生日礼物，预算500元。
RecommendationResult.intent.scenario = 生日
RecommendationResult.intent.budget = 500
返回商品数量 > 0

输入：见家长，预算3000，体面点
RecommendationResult.intent.scenario = 见家长
RecommendationResult.intent.budget = 3000
返回商品数量 > 0
```

后续可继续做：

- 将 `GiftIntent` 暴露到调试接口，方便前端或测试查看解析结果。
- 为 `IntentExtractor.extract_with_rules` 增加单元测试。
- 在 R2 商品规则打分器中直接使用 `GiftIntent`。
