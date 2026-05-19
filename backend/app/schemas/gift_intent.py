from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator


BudgetLevel = Literal["low", "mid", "high", "luxury"]


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

        missing: list[str] = []
        if not self.recipient and not self.target_people:
            missing.append("recipient")
        if not self.scenario and not self.scenarios:
            missing.append("scenario")
        if self.budget is None and self.budget_min is None and self.budget_max is None:
            missing.append("budget")
        self.missing_slots = list(dict.fromkeys([*self.missing_slots, *missing]))

        # 如果关键信息少于两个，建议先追问；只有预算缺失时仍可先给分档推荐。
        critical_missing = [slot for slot in self.missing_slots if slot in {"recipient", "scenario"}]
        self.must_ask = self.must_ask or len(critical_missing) > 0
        return self

