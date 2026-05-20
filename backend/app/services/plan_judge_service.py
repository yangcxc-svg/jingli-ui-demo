from __future__ import annotations

from app.schemas.recommendation import RecommendationPlan


class PlanJudgeService:
    """Choose the final recommendation plan with deterministic rules."""

    COMBO_MARKERS = ("组合", "礼单", "搭配", "一套", "多个", "凑")

    def choose(
        self,
        *,
        message: str,
        plans: list[RecommendationPlan],
    ) -> RecommendationPlan | None:
        if not plans:
            return None
        ranked = self._find(plans, "ranked_topn") or plans[0]
        optimized = self._find(plans, "budget_optimized")
        if optimized is None:
            return ranked.model_copy(update={"judge_reason": "当前只有默认相关度排序方案可用"})

        if self._exceeds_upper_bound(ranked) and not self._exceeds_upper_bound(optimized):
            return optimized.model_copy(update={"judge_reason": "默认方案超过预算上限，选择预算约束内的优化方案"})

        if any(marker in message for marker in self.COMBO_MARKERS):
            return optimized.model_copy(update={"judge_reason": "用户表达了组合或搭配需求，选择预算优化组合方案"})

        ranked_usage = ranked.budget_usage or 0.0
        optimized_usage = optimized.budget_usage or 0.0
        ranked_relevance = ranked.relevance_score
        optimized_relevance = optimized.relevance_score

        if ranked.original_budget is not None:
            relevance_close = optimized_relevance >= ranked_relevance * 0.72
            usage_better = optimized_usage >= max(ranked_usage + 0.18, 0.55)
            if ranked_usage < 0.55 and usage_better and relevance_close:
                return optimized.model_copy(
                    update={"judge_reason": "组合方案相关度接近默认方案，且预算利用更合理"}
                )

        if optimized_relevance < ranked_relevance * 0.62:
            return ranked.model_copy(update={"judge_reason": "预算组合方案相关度下降较多，保留默认推荐"})

        if optimized.objective_score > ranked.objective_score + 0.06:
            return optimized.model_copy(update={"judge_reason": "组合方案综合目标函数更高"})

        return ranked.model_copy(update={"judge_reason": "默认相关度排序方案更稳妥"})

    @staticmethod
    def _find(plans: list[RecommendationPlan], plan_type: str) -> RecommendationPlan | None:
        return next((plan for plan in plans if plan.plan_type == plan_type), None)

    @staticmethod
    def _exceeds_upper_bound(plan: RecommendationPlan) -> bool:
        return plan.budget_upper_bound is not None and plan.total_price > plan.budget_upper_bound
