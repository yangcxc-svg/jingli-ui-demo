from __future__ import annotations

import json
import logging
import re
from decimal import Decimal
from typing import Any

from app.agent.prompts import INTENT_EXTRACTION_PROMPT_VERSION
from app.agent.prompts_lib.intent_extraction import (
    INTENT_EXTRACTION_SYSTEM_PROMPT,
    build_intent_extraction_prompt,
)
from app.llm.client import LLMClient
from app.schemas.gift_intent import BudgetConstraintType, GiftIntent, infer_budget_level

logger = logging.getLogger(__name__)


class IntentExtractor:
    def __init__(self) -> None:
        self.llm = LLMClient()

    async def extract(self, message: str) -> GiftIntent:
        fallback = self.extract_with_rules(message)
        if self.llm.is_mock:
            return fallback

        result = await self.llm.generate(
            build_intent_extraction_prompt(message),
            system=INTENT_EXTRACTION_SYSTEM_PROMPT,
            temperature=0.1,
            prompt_name="intent_extraction",
            prompt_version=INTENT_EXTRACTION_PROMPT_VERSION,
        )
        parsed = self._parse_json_object(result.text)
        if parsed is None:
            logger.warning("intent_extraction_invalid_json text=%r", result.text[:300])
            return fallback

        try:
            intent = GiftIntent.model_validate(parsed)
        except Exception as exc:  # noqa: BLE001
            logger.warning("intent_extraction_validation_failed err=%s", exc)
            return fallback

        return self._merge_with_fallback(intent, fallback)

    def extract_with_rules(self, message: str) -> GiftIntent:
        budget = self._extract_budget(message)
        budget_constraint_type = self._extract_budget_constraint_type(message, budget)
        budget_flexibility = self._budget_flexibility(budget_constraint_type) if budget else None
        scenario = self._extract_scenario(message)
        recipient, relationship, target_people = self._extract_recipient(message, scenario)
        gift_style = self._extract_keywords(
            message,
            ["体面", "有心意", "颜值高", "实用", "健康", "浪漫", "稳重", "高端", "商务", "科技感", "喜庆", "性价比"],
        )
        preferences = self._extract_keywords(
            message,
            ["咖啡", "茶", "运动", "美妆", "护肤", "数码", "投影", "按摩", "养生", "香氛", "家电"],
        )
        avoid = self._extract_avoid(message)
        scenarios = [scenario] if scenario else []

        return GiftIntent(
            recipient=recipient,
            relationship=relationship,
            scenario=scenario,
            budget=budget,
            budget_constraint_type=budget_constraint_type,
            budget_flexibility=budget_flexibility,
            budget_reason=self._budget_reason(message, budget, budget_constraint_type),
            preferences=preferences,
            avoid=avoid,
            gift_style=gift_style,
            target_people=target_people,
            scenarios=scenarios,
            budget_level=infer_budget_level(budget),
        )

    @staticmethod
    def _parse_json_object(text: str) -> dict[str, Any] | None:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
            stripped = re.sub(r"```$", "", stripped).strip()

        candidates = [stripped]
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidates.append(stripped[start : end + 1])

        for candidate in candidates:
            try:
                value = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
        return None

    @staticmethod
    def _extract_budget(message: str) -> Decimal | None:
        patterns = [
            r"预算\s*(\d{2,6})",
            r"(\d{2,6})\s*元",
            r"(\d{2,6})\s*块",
        ]
        matches: list[str] = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, message))
        if not matches:
            return None
        return Decimal(matches[-1])

    @classmethod
    def _extract_budget_constraint_type(
        cls,
        message: str,
        budget: Decimal | None,
    ) -> BudgetConstraintType:
        if budget is None:
            return "unknown"
        hard_markers = ("以内", "不超过", "别超过", "最多", "上限", "封顶", "不能超")
        negotiable_markers = (
            "可以再加一点",
            "可加一点",
            "能加一点",
            "预算可以加",
            "预算可加",
            "可以加",
            "能加",
            "放宽",
        )
        soft_markers = ("左右", "大概", "差不多", "上下", "附近", "约", "大约")
        if any(marker in message for marker in hard_markers):
            return "hard"
        if any(marker in message for marker in negotiable_markers):
            return "negotiable"
        if any(marker in message for marker in soft_markers):
            return "soft"
        return "unknown"

    @staticmethod
    def _budget_flexibility(constraint_type: BudgetConstraintType) -> float:
        if constraint_type == "hard":
            return 0.0
        if constraint_type == "soft":
            return 0.15
        if constraint_type == "negotiable":
            return 0.30
        return 0.15

    @classmethod
    def _budget_reason(
        cls,
        message: str,
        budget: Decimal | None,
        constraint_type: BudgetConstraintType,
    ) -> str | None:
        if budget is None:
            return None
        if constraint_type == "hard":
            return "用户使用了以内/不超过/最多等表达，预算作为硬约束。"
        if constraint_type == "soft":
            return "用户使用了左右/大概/差不多等表达，预算允许小幅浮动。"
        if constraint_type == "negotiable":
            return "用户表达预算可以加一点或可放宽，预算允许更大浮动。"
        return "用户只给出预算数字，默认作为可小幅浮动的参考预算。"

    @staticmethod
    def _extract_scenario(message: str) -> str | None:
        scenario_aliases = [
            ("见家长", ["见家长", "见父母", "第一次上门", "拜访父母", "对象父母"]),
            ("生日", ["生日", "生辰"]),
            ("情侣纪念日", ["纪念日", "周年", "情人节", "七夕"]),
            ("送领导/客户", ["领导", "客户", "商务", "合作伙伴"]),
            ("乔迁", ["乔迁", "新居", "搬家", "入住"]),
            ("探望长辈", ["探望", "看望", "长辈", "爸妈", "父母", "老人"]),
            ("婚礼/订婚", ["婚礼", "订婚", "结婚", "婚庆"]),
            ("节日送礼", ["春节", "中秋", "端午", "节日", "过年"]),
        ]
        for canonical, aliases in scenario_aliases:
            if any(alias in message for alias in aliases):
                return canonical
        return None

    @staticmethod
    def _extract_recipient(message: str, scenario: str | None) -> tuple[str | None, str | None, list[str]]:
        if scenario == "见家长":
            return "对象父母", "长辈关系", ["长辈", "父母", "对象父母"]
        if "女朋友" in message:
            return "女朋友", "亲密关系", ["女朋友", "女生"]
        if "女生" in message:
            return "女生", "朋友关系", ["女生"]
        if "男朋友" in message:
            return "男朋友", "亲密关系", ["男朋友"]
        if any(word in message for word in ["爸妈", "父母", "妈妈", "爸爸"]):
            return "父母", "长辈关系", ["父母", "长辈"]
        if "长辈" in message or "老人" in message:
            return "长辈", "长辈关系", ["长辈"]
        if "领导" in message:
            return "领导", "商务关系", ["领导", "商务"]
        if "客户" in message:
            return "客户", "商务关系", ["客户", "商务"]
        if "同事" in message:
            return "同事", "职场关系", ["同事"]
        if "朋友" in message:
            return "朋友", "朋友关系", ["朋友"]
        return None, None, []

    @staticmethod
    def _extract_keywords(message: str, candidates: list[str]) -> list[str]:
        return [item for item in candidates if item in message]

    @staticmethod
    def _extract_avoid(message: str) -> list[str]:
        avoid: list[str] = []
        for marker in ["不要", "不想", "避免", "别"]:
            if marker in message:
                tail = message.split(marker, 1)[1].strip(" ，。,.")
                if tail:
                    avoid.append(tail[:24])
        return avoid

    @staticmethod
    def _merge_with_fallback(intent: GiftIntent, fallback: GiftIntent) -> GiftIntent:
        data = intent.model_dump()
        for key in [
            "recipient",
            "relationship",
            "scenario",
            "budget",
            "budget_min",
            "budget_max",
            "budget_flexibility",
            "budget_upper_bound",
            "budget_reason",
            "budget_level",
        ]:
            if data.get(key) in (None, ""):
                data[key] = getattr(fallback, key)
        if (
            data.get("budget_constraint_type") in (None, "", "unknown")
            and fallback.budget_constraint_type != "unknown"
        ):
            data["budget_constraint_type"] = fallback.budget_constraint_type
            data["budget_flexibility"] = fallback.budget_flexibility
            data["budget_upper_bound"] = fallback.budget_upper_bound
            data["budget_reason"] = fallback.budget_reason
        for key in ["preferences", "avoid", "gift_style", "target_people", "scenarios"]:
            merged = [*getattr(intent, key), *getattr(fallback, key)]
            data[key] = list(dict.fromkeys(item for item in merged if item))
        return GiftIntent.model_validate(data)
