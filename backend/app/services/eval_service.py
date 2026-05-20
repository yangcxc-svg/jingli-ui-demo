"""Evaluation service for recommendation quality and observability."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4

from app.metrics.collector import MetricsCollector
from app.schemas.gift_intent import GiftIntent
from app.schemas.product import ProductCard
from app.schemas.recommendation import RecommendationRequest, RecommendationStrategy
from app.schemas.eval import EvalRunResponse, EvalSummaryResponse
from app.services.recommendation_service import RecommendationService
from app.services.seed_product_loader import seed_product_catalog


@dataclass(frozen=True)
class RecommendationEvalCase:
    case_id: str
    message: str
    intent: GiftIntent
    expected_scenarios: list[str] = field(default_factory=list)
    expected_target_people: list[str] = field(default_factory=list)
    budget: Decimal | None = None
    avoid_keywords: list[str] = field(default_factory=list)
    should_clarify: bool = False
    should_relax: bool = False


GOLDEN_RECOMMENDATION_CASES: list[RecommendationEvalCase] = [
    RecommendationEvalCase(
        case_id="birthday_girlfriend_500",
        message="给女朋友生日礼物，预算500，要有心意",
        intent=GiftIntent(
            recipient="女朋友",
            relationship="亲密关系",
            scenario="生日",
            budget=Decimal("500"),
            preferences=["有心意"],
            gift_style=["有心意", "颜值高"],
            target_people=["女朋友", "女生"],
            scenarios=["生日"],
        ),
        expected_scenarios=["生日"],
        expected_target_people=["女朋友", "女生"],
        budget=Decimal("500"),
    ),
    RecommendationEvalCase(
        case_id="birthday_girlfriend_500_hard_budget",
        message="给女朋友生日礼物，预算500以内，要有心意",
        intent=GiftIntent(
            recipient="女朋友",
            relationship="亲密关系",
            scenario="生日",
            budget=Decimal("500"),
            budget_constraint_type="hard",
            preferences=["有心意"],
            gift_style=["有心意", "颜值高"],
            target_people=["女朋友", "女生"],
            scenarios=["生日"],
        ),
        expected_scenarios=["生日"],
        expected_target_people=["女朋友", "女生"],
        budget=Decimal("500"),
    ),
    RecommendationEvalCase(
        case_id="birthday_girlfriend_500_negotiable_combo",
        message="给女朋友生日礼物，预算500左右，可以再加一点，想搭配一套",
        intent=GiftIntent(
            recipient="女朋友",
            relationship="亲密关系",
            scenario="生日",
            budget=Decimal("500"),
            budget_constraint_type="negotiable",
            preferences=["有心意"],
            gift_style=["有心意", "颜值高"],
            target_people=["女朋友", "女生"],
            scenarios=["生日"],
        ),
        expected_scenarios=["生日"],
        expected_target_people=["女朋友", "女生"],
        budget=Decimal("650"),
    ),
    RecommendationEvalCase(
        case_id="meet_parents_3000",
        message="第一次见家长，预算3000，体面点",
        intent=GiftIntent(
            recipient="对象父母",
            relationship="长辈关系",
            scenario="见家长",
            budget=Decimal("3000"),
            gift_style=["体面", "正式"],
            target_people=["长辈", "父母", "对象父母"],
            scenarios=["见家长"],
        ),
        expected_scenarios=["见家长"],
        expected_target_people=["长辈", "父母", "对象父母"],
        budget=Decimal("3000"),
    ),
    RecommendationEvalCase(
        case_id="leader_not_offensive",
        message="送领导，不想太冒犯，预算1000",
        intent=GiftIntent(
            recipient="领导",
            relationship="商务关系",
            scenario="送领导/客户",
            budget=Decimal("1000"),
            avoid=["太冒犯", "过度亲密"],
            gift_style=["稳重", "商务"],
            target_people=["领导", "商务"],
            scenarios=["送领导/客户"],
        ),
        expected_scenarios=["送领导/客户"],
        expected_target_people=["领导", "商务"],
        budget=Decimal("1000"),
        avoid_keywords=["情侣", "浪漫", "亲密"],
    ),
    RecommendationEvalCase(
        case_id="housewarming_practical",
        message="乔迁礼物，实用一点，预算800",
        intent=GiftIntent(
            recipient="朋友",
            relationship="朋友关系",
            scenario="乔迁",
            budget=Decimal("800"),
            gift_style=["实用"],
            target_people=["朋友"],
            scenarios=["乔迁"],
        ),
        expected_scenarios=["乔迁"],
        expected_target_people=["朋友"],
        budget=Decimal("800"),
    ),
    RecommendationEvalCase(
        case_id="elder_health",
        message="探望长辈，健康相关，预算1500",
        intent=GiftIntent(
            recipient="长辈",
            relationship="长辈关系",
            scenario="探望长辈",
            budget=Decimal("1500"),
            preferences=["养生"],
            gift_style=["健康", "实用"],
            target_people=["长辈"],
            scenarios=["探望长辈"],
        ),
        expected_scenarios=["探望长辈"],
        expected_target_people=["长辈"],
        budget=Decimal("1500"),
    ),
    RecommendationEvalCase(
        case_id="vague_need_clarification",
        message="推荐个礼物",
        intent=GiftIntent(),
        should_clarify=True,
    ),
    RecommendationEvalCase(
        case_id="low_budget_needs_relaxation",
        message="给女朋友生日礼物，预算100元，要有心意",
        intent=GiftIntent(
            recipient="女朋友",
            relationship="亲密关系",
            scenario="生日",
            budget=Decimal("100"),
            preferences=["有心意"],
            gift_style=["有心意"],
            target_people=["女朋友", "女生"],
            scenarios=["生日"],
        ),
        expected_scenarios=["生日"],
        expected_target_people=["女朋友", "女生"],
        budget=Decimal("100"),
        should_relax=True,
    ),
]


class EvalService:
    def __init__(self) -> None:
        self.metrics = MetricsCollector()

    async def run(self, strategy: RecommendationStrategy = "hybrid_algorithm") -> EvalRunResponse:
        seed_product_catalog.load()
        service = RecommendationService()
        service.intent_extractor.llm.provider = "mock"
        service.llm.provider = "mock"

        eval_run_id = str(uuid4())
        executed = 0
        failures = 0
        case_results: list[dict[str, object]] = []

        for case in GOLDEN_RECOMMENDATION_CASES:
            try:
                result = await service.recommend_products(
                    RecommendationRequest(
                        message=case.message,
                        conversation_id=f"eval-{eval_run_id}-{case.case_id}",
                        max_products=4,
                        max_candidates=20,
                        include_fallback=True,
                        strategy=strategy,
                        gift_intent=case.intent,
                        allow_generic_recommendation=False,
                        use_profile=False,
                    )
                )
                case_result = self._evaluate_case(eval_run_id, strategy, case, result)
                case_results.append(case_result)
                executed += 1
            except Exception as exc:  # noqa: BLE001
                failures += 1
                case_results.append(
                    {
                        "case_id": case.case_id,
                        "query": case.message,
                        "error": str(exc),
                    }
                )

        metrics = self._summarize_case_results(case_results)
        return EvalRunResponse(
            eval_run_id=eval_run_id,
            status="done" if failures == 0 else "partial",
            executed=executed,
            failures=failures,
            metrics=metrics,
            cases=case_results,
        )

    async def summary(self) -> EvalSummaryResponse:
        snap = self.metrics.snapshot()
        status = "ready" if int(snap.get("recommendation_eval_total", 0) or 0) > 0 else "empty"
        return EvalSummaryResponse(
            status=status,
            metrics=snap,
            recent=self.metrics.recent_recommendation_evals(n=12),
        )

    def _evaluate_case(
        self,
        eval_run_id: str,
        strategy: RecommendationStrategy,
        case: RecommendationEvalCase,
        result,
    ) -> dict[str, object]:
        products = result.products
        top_product_ids = [item.product_id for item in products]
        scenario_hit = self._scenario_hit(products, case.expected_scenarios)
        target_hit = self._target_hit(products, case.expected_target_people)
        budget_hit = self._budget_hit(products, case.budget)
        avoid_violation = self._avoid_violation(products, case.avoid_keywords)
        duplicate_count = len(top_product_ids) - len(set(top_product_ids))
        clarification_ok = result.needs_clarification == case.should_clarify
        relaxation_ok = result.needs_relaxation == case.should_relax
        candidate_count = int(result.pipeline.get("candidate_count") or 0)
        selected_budget_usage = result.pipeline.get("selected_plan_budget_usage")

        self.metrics.record_recommendation_eval(
            eval_run_id=eval_run_id,
            case_id=case.case_id,
            query=case.message,
            strategy=strategy,
            returned_count=len(products),
            candidate_count=candidate_count,
            needs_clarification=result.needs_clarification,
            scenario_hit=scenario_hit,
            target_hit=target_hit,
            budget_hit=budget_hit,
            avoid_violation=avoid_violation,
            duplicate_count=duplicate_count,
            top_product_ids=top_product_ids,
        )

        return {
            "case_id": case.case_id,
            "query": case.message,
            "strategy": strategy,
            "needs_clarification": result.needs_clarification,
            "clarification_ok": clarification_ok,
            "clarification_question": result.clarification_question,
            "needs_relaxation": result.needs_relaxation,
            "relaxation_ok": relaxation_ok,
            "relaxation_reason": result.relaxation_reason,
            "relaxation_options": [item.model_dump(mode="json") for item in result.relaxation_options],
            "suggested_questions": result.suggested_questions,
            "selected_plan_id": result.selected_plan_id,
            "selected_plan_type": result.selected_plan_type,
            "plan_judge_reason": result.plan_judge_reason,
            "plans": [
                {
                    "plan_id": plan.plan_id,
                    "plan_type": plan.plan_type,
                    "product_ids": plan.product_ids,
                    "total_price": str(plan.total_price),
                    "original_budget": str(plan.original_budget) if plan.original_budget is not None else None,
                    "budget_upper_bound": (
                        str(plan.budget_upper_bound) if plan.budget_upper_bound is not None else None
                    ),
                    "budget_constraint_type": plan.budget_constraint_type,
                    "budget_usage": plan.budget_usage,
                    "upper_bound_usage": plan.upper_bound_usage,
                    "budget_overage": str(plan.budget_overage),
                    "budget_overage_ratio": plan.budget_overage_ratio,
                    "gift_roles": plan.gift_roles,
                    "relevance_score": plan.relevance_score,
                    "diversity_score": plan.diversity_score,
                    "complement_score": plan.complement_score,
                    "objective_score": plan.objective_score,
                    "judge_reason": plan.judge_reason,
                }
                for plan in result.plans
            ],
            "top_product_ids": top_product_ids,
            "top_products": [
                {
                    "product_id": item.product_id,
                    "name": item.name,
                    "price": str(item.price) if item.price is not None else None,
                    "reason": item.display_reason or item.reason,
                }
                for item in products
            ],
            "intent": result.intent.model_dump(mode="json") if result.intent else None,
            "pipeline": result.pipeline,
            "checks": {
                "scenario_hit": scenario_hit,
                "target_hit": target_hit,
                "budget_hit": budget_hit,
                "avoid_violation": avoid_violation,
                "duplicate_count": duplicate_count,
                "needs_relaxation": result.needs_relaxation,
                "selected_plan_budget_usage": selected_budget_usage,
                "selected_plan_budget_constraint_type": result.pipeline.get(
                    "selected_plan_budget_constraint_type"
                ),
                "selected_plan_budget_overage_ratio": result.pipeline.get(
                    "selected_plan_budget_overage_ratio"
                ),
                "selected_plan_type": result.selected_plan_type,
            },
        }

    @staticmethod
    def _scenario_hit(products: list[ProductCard], expected: list[str]) -> bool:
        if not expected:
            return True
        expected_set = set(expected)
        return any(expected_set & set(item.scenarios) for item in products)

    @staticmethod
    def _target_hit(products: list[ProductCard], expected: list[str]) -> bool:
        if not expected:
            return True
        expected_set = set(expected)
        return any(expected_set & set(item.target_people) for item in products)

    @staticmethod
    def _budget_hit(products: list[ProductCard], budget: Decimal | None) -> bool:
        if budget is None:
            return True
        if not products:
            return False
        return all(item.price is not None and item.price <= budget * Decimal("1.15") for item in products)

    @staticmethod
    def _avoid_violation(products: list[ProductCard], avoid_keywords: list[str]) -> bool:
        if not avoid_keywords:
            return False
        joined = " ".join(
            " ".join(
                [
                    item.name,
                    " ".join(item.tags),
                    " ".join(item.highlights),
                    " ".join(item.scenarios),
                    " ".join(item.target_people),
                ]
            )
            for item in products
        )
        return any(keyword and keyword in joined for keyword in avoid_keywords)

    @staticmethod
    def _summarize_case_results(cases: list[dict[str, object]]) -> dict[str, object]:
        valid = [case for case in cases if "checks" in case]
        if not valid:
            return {"case_count": 0}
        total = len(valid)
        checks = [case["checks"] for case in valid if isinstance(case["checks"], dict)]
        return {
            "case_count": total,
            "scenario_hit_rate": round(
                sum(1 for item in checks if item.get("scenario_hit")) / total,
                4,
            ),
            "target_hit_rate": round(
                sum(1 for item in checks if item.get("target_hit")) / total,
                4,
            ),
            "budget_hit_rate": round(
                sum(1 for item in checks if item.get("budget_hit")) / total,
                4,
            ),
            "avoid_violation_rate": round(
                sum(1 for item in checks if item.get("avoid_violation")) / total,
                4,
            ),
            "clarification_accuracy": round(
                sum(1 for case in valid if case.get("clarification_ok")) / total,
                4,
            ),
            "duplicate_case_rate": round(
                sum(1 for item in checks if int(item.get("duplicate_count") or 0) > 0) / total,
                4,
            ),
            "relaxation_accuracy": round(
                sum(1 for case in valid if case.get("relaxation_ok")) / total,
                4,
            ),
            "relaxation_rate": round(
                sum(1 for item in checks if item.get("needs_relaxation")) / total,
                4,
            ),
            "budget_optimized_selection_rate": round(
                sum(
                    1
                    for item in checks
                    if item.get("selected_plan_type") == "budget_optimized"
                )
                / total,
                4,
            ),
            "avg_selected_budget_usage": round(
                sum(
                    float(item.get("selected_plan_budget_usage") or 0)
                    for item in checks
                    if item.get("selected_plan_budget_usage") is not None
                )
                / max(
                    sum(
                        1
                        for item in checks
                        if item.get("selected_plan_budget_usage") is not None
                    ),
                    1,
                ),
                4,
            ),
            "avg_returned_count": round(
                sum(len(case.get("top_product_ids") or []) for case in valid) / total,
                2,
            ),
        }
