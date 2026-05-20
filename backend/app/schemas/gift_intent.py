from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


BudgetLevel = Literal["low", "mid", "high", "luxury"]
BudgetConstraintType = Literal["hard", "soft", "negotiable", "unknown"]


def infer_budget_level(budget: Decimal | None) -> BudgetLevel | None:
    if budget is None:
        return None
    if budget < Decimal("500"):
        return "low"
    if budget < Decimal("3000"):
        return "mid"
    if budget < Decimal("10000"):
        return "high"
    return "luxury"


class GiftIntent(BaseModel):
    recipient: str | None = None
    relationship: str | None = None
    scenario: str | None = None
    budget: Decimal | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    budget_constraint_type: BudgetConstraintType = "unknown"
    budget_flexibility: float | None = None
    budget_upper_bound: Decimal | None = None
    budget_reason: str | None = None
    preferences: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    gift_style: list[str] = Field(default_factory=list)
    target_people: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    budget_level: BudgetLevel | None = None
    must_ask: bool = False
    missing_slots: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize(self) -> "GiftIntent":
        if self.scenario and self.scenario not in self.scenarios:
            self.scenarios.append(self.scenario)
        if self.recipient and self.recipient not in self.target_people:
            self.target_people.append(self.recipient)
        if self.budget_level is None:
            self.budget_level = infer_budget_level(self.budget)
        if self.budget is not None:
            # Let the model/rules decide the semantic type, but compute the numeric
            # bound deterministically so "hard" never accidentally becomes soft.
            self.budget_flexibility = self._default_budget_flexibility(
                self.budget_constraint_type
            )
            multiplier = Decimal("1") + Decimal(str(self.budget_flexibility or 0))
            self.budget_upper_bound = (self.budget * multiplier).quantize(Decimal("1"))
            if self.budget_reason is None:
                self.budget_reason = self._default_budget_reason(
                    self.budget_constraint_type,
                    self.budget,
                    self.budget_upper_bound,
                )

        missing: list[str] = []
        if not self.recipient and not self.target_people:
            missing.append("recipient")
        if not self.scenario and not self.scenarios:
            missing.append("scenario")
        if self.budget is None and self.budget_min is None and self.budget_max is None:
            missing.append("budget")
        provided_missing: list[str] = []
        if (
            "preference" in self.missing_slots
            and not self.preferences
            and not self.gift_style
            and not self.avoid
        ):
            provided_missing.append("preference")
        self.missing_slots = list(dict.fromkeys([*provided_missing, *missing]))

        # 如果关键信息少于两个，建议先追问；只有预算缺失时仍可先给分档推荐。
        critical_missing = [slot for slot in self.missing_slots if slot in {"recipient", "scenario"}]
        self.must_ask = len(critical_missing) > 0
        return self

    @staticmethod
    def _default_budget_flexibility(constraint_type: BudgetConstraintType) -> float:
        if constraint_type == "hard":
            return 0.0
        if constraint_type == "soft":
            return 0.15
        if constraint_type == "negotiable":
            return 0.30
        return 0.15

    @staticmethod
    def _default_budget_reason(
        constraint_type: BudgetConstraintType,
        budget: Decimal,
        upper_bound: Decimal | None,
    ) -> str:
        if constraint_type == "hard":
            return f"用户表达了明确上限，预算约束固定为 {budget} 元。"
        if constraint_type == "soft":
            return f"用户表达为大概预算，可在 {budget} 元基础上小幅浮动到 {upper_bound} 元。"
        if constraint_type == "negotiable":
            return f"用户表达预算可协商，可在 {budget} 元基础上放宽到 {upper_bound} 元。"
        return f"用户给出预算 {budget} 元，未说明是否严格，默认允许小幅浮动到 {upper_bound} 元。"
