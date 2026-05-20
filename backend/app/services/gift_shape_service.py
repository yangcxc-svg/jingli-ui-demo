from __future__ import annotations

from decimal import Decimal

from app.schemas.gift_intent import GiftIntent
from app.schemas.gift_solution import GiftShapeDecision


class GiftShapeService:
    """Decide whether a gift request should be handled as a single gift or combo."""

    _FORCE_COMBO = ("组合", "礼单", "搭配", "一套", "多个", "几件", "配一")
    _FORCE_SINGLE = ("一个", "一件", "单品", "不要复杂", "简单点", "简单一点", "别太复杂")
    _FORMAL_SCENARIOS = {"见家长", "婚礼/订婚", "送领导/客户", "探望长辈", "节日送礼"}
    _LIGHT_SCENARIOS = {"生日", "日常关怀"}
    _COMBO_STYLES = {"体面", "高端", "正式", "稳重", "健康", "实用"}

    def decide(self, *, message: str, intent: GiftIntent) -> GiftShapeDecision:
        signals: list[str] = []

        if any(marker in message for marker in self._FORCE_SINGLE):
            return GiftShapeDecision(
                shape="single_gift",
                confidence=0.92,
                reason="用户明确表达希望简单或单件礼物，不应强行组合。",
                signals=["用户明确要求单品"],
                recommended_product_count=3,
                use_combo_optimizer=False,
            )

        if any(marker in message for marker in self._FORCE_COMBO):
            return GiftShapeDecision(
                shape="gift_combo",
                confidence=0.94,
                reason="用户明确表达组合、礼单或搭配需求。",
                signals=["用户明确要求组合"],
                recommended_product_count=3,
                use_combo_optimizer=True,
            )

        score = 0
        if set(intent.scenarios) & self._FORMAL_SCENARIOS:
            score += 3
            signals.append("正式或高压送礼场景")
        if intent.budget is not None and intent.budget >= Decimal("1000"):
            score += 2
            signals.append("预算足以支撑组合礼品")
        elif intent.budget is not None and intent.budget < Decimal("500"):
            score -= 2
            signals.append("预算较低，单品更稳妥")
        if set(intent.gift_style) & self._COMBO_STYLES:
            score += 1
            signals.append("用户强调体面、实用或健康等多目标")
        if len([*intent.preferences, *intent.gift_style]) >= 3:
            score += 1
            signals.append("用户目标较多，组合更容易覆盖")
        if set(intent.scenarios) & self._LIGHT_SCENARIOS and (intent.budget or Decimal("0")) < Decimal("800"):
            score -= 1
            signals.append("轻量场景更适合克制表达")

        if score >= 3:
            return GiftShapeDecision(
                shape="gift_combo",
                confidence=min(0.72 + score * 0.04, 0.9),
                reason="根据场景、预算和风格诉求，组合礼品更能体现完整度。",
                signals=signals,
                recommended_product_count=3,
                use_combo_optimizer=True,
            )
        if score <= 0:
            return GiftShapeDecision(
                shape="single_gift",
                confidence=0.72,
                reason="当前需求更适合选择一个清晰、克制的主礼。",
                signals=signals or ["未出现组合强信号"],
                recommended_product_count=3,
                use_combo_optimizer=False,
            )
        return GiftShapeDecision(
            shape="either",
            confidence=0.62,
            reason="单品和组合都可行，默认按更稳妥的单品推荐，并保留切换组合空间。",
            signals=signals,
            recommended_product_count=3,
            use_combo_optimizer=False,
        )
