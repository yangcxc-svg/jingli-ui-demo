"""Prompt 注册表（按场景拆分）。

历史上 `app.agent.prompts` 只有一份 `GUIDE_SYSTEM_PROMPT`。任务 6 将其按场景拆分，
但为了保持向后兼容，**模块路径与名称不变**，内部按 section 注释组织：

- guide_system 段：通用导购 system prompt
- chat_recommendation 段：聊天推荐用户态拼接
- gift_plan 段：组合礼单结构化输出 prompt + JSON schema
- product_rerank 段：预留商品重排序 prompt

场景化模板与拼接函数集中在 `app.agent.prompts_lib` 子包，本文件仅做 re-export，
让 `from app.agent.prompts import GUIDE_SYSTEM_PROMPT` 等老调用方继续工作。
"""

from __future__ import annotations

# ---- prompt 版本号（保持向后兼容） ----

INTENT_PROMPT_VERSION = "intent-v1"
RAG_PROMPT_VERSION = "rag-v1"
RECOMMENDATION_PROMPT_VERSION = "recommendation-v1"

# 任务 6 新增版本号
GIFT_PLAN_PROMPT_VERSION = "gift-plan-v1"
CHAT_RECOMMENDATION_PROMPT_VERSION = "chat-recommendation-v1"
INTENT_EXTRACTION_PROMPT_VERSION = "intent-extraction-v1"

# ---- 通用导购 system prompt ----

# 沿用既有文案，老调用方 `from app.agent.prompts import GUIDE_SYSTEM_PROMPT` 不变。
from app.agent.prompts_lib.guide_system import GUIDE_SYSTEM_PROMPT  # noqa: E402,F401

# ---- 场景化模板与拼接函数 re-export ----

from app.agent.prompts_lib.chat_recommendation import (  # noqa: E402,F401
    CHAT_RECOMMENDATION_INSTRUCTION,
    build_chat_recommendation_prompt,
)
from app.agent.prompts_lib.gift_plan import (  # noqa: E402,F401
    GIFT_PLAN_STRUCTURED_INSTRUCTION,
    GIFT_PLAN_JSON_SCHEMA_HINT,
    build_gift_plan_prompt,
)
from app.agent.prompts_lib.intent_extraction import (  # noqa: E402,F401
    INTENT_EXTRACTION_SYSTEM_PROMPT,
    build_intent_extraction_prompt,
)
from app.agent.prompts_lib.product_rerank import (  # noqa: E402,F401
    PRODUCT_RERANK_PROMPT,
)

__all__ = [
    "INTENT_PROMPT_VERSION",
    "RAG_PROMPT_VERSION",
    "RECOMMENDATION_PROMPT_VERSION",
    "GIFT_PLAN_PROMPT_VERSION",
    "CHAT_RECOMMENDATION_PROMPT_VERSION",
    "INTENT_EXTRACTION_PROMPT_VERSION",
    "GUIDE_SYSTEM_PROMPT",
    "CHAT_RECOMMENDATION_INSTRUCTION",
    "build_chat_recommendation_prompt",
    "GIFT_PLAN_STRUCTURED_INSTRUCTION",
    "GIFT_PLAN_JSON_SCHEMA_HINT",
    "build_gift_plan_prompt",
    "INTENT_EXTRACTION_SYSTEM_PROMPT",
    "build_intent_extraction_prompt",
    "PRODUCT_RERANK_PROMPT",
]
